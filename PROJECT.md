# AI Voice Agent — Project Documentation

This document explains what the project is, how it is built, and exactly how data flows
through it. For development rules and philosophy see `CLAUDE.md`. For the original
spec see `AI Voice Agent for Phone Call Automation.md`. This file is kept up to date
as the project grows — it describes the system as it actually exists right now.

---

## 1. What this project is

A local, zero-cost AI voice agent, built as a college project, that can:

- Hold a spoken, multi-turn conversation (voice in → voice out).
- Act as a **Personal Assistant** (answer calls, take messages, callbacks).
- Act as a **Sales Agent** (qualify leads, score interest).
- Eventually take real phone calls through a telephony provider.

Everything currently runs **locally on one machine** — no cloud APIs, no paid
services. A real phone call is a later phase; today the "phone" is your
microphone and speakers in the browser.

---

## 2. Tech stack (what's actually installed and used)

| Layer | Technology | Notes |
|---|---|---|
| Backend | Python + FastAPI | single app, no microservices |
| LLM | Ollama, model `qwen3:8b` | local, runs on `localhost:11434` |
| Speech-to-Text | `faster-whisper`, model `base` | runs on CPU, int8 |
| Text-to-Speech | `piper-tts`, voice `en_US-lessac-medium` | runs on CPU |
| Database | SQLite | not yet implemented (Phase 8) |
| Frontend | Plain HTML / CSS / JS | single page, no framework |

Nothing is trained — all models are pre-trained, downloaded once, and run
locally through their respective libraries.

---

## 3. Project structure

```
ai-voice-agent/
│
├── app/
│   ├── main.py        FastAPI app: routes, request/response models
│   ├── agent.py         Personal Assistant logic: intent, actions, call state
│   ├── prompts.py        System prompts (currently: personal assistant prompt)
│   ├── llm.py          Talks to Ollama (chat completion)
│   ├── stt.py          Talks to faster-whisper (audio -> text)
│   ├── tts.py           Talks to piper-tts (text -> audio)
│
├── frontend/
│   ├── index.html      Chat UI + mic button + audio playback
│   └── style.css
│
├── data/
│   └── voices/          Downloaded Piper voice model (git-ignored, ~60MB)
│
├── requirements.txt
├── .env.example         Copy to .env (git-ignored)
├── CLAUDE.md             Development rules (read this first)
├── README.md             Quick start + status table
└── PROJECT.md             This file
```

`app/database.py` from the target structure in `CLAUDE.md` doesn't exist yet
— it arrives in Phase 8, when in-memory state (see `app/agent.py`) moves to
SQLite.

---

## 4. How each module works

### `app/agent.py` + `app/prompts.py` — the personality (Personal Assistant)

This is what actually drives the conversation now — `/api/chat` no longer
talks to `app/llm.py` directly, it goes through `agent.handle_message()`.

- `app/prompts.py` holds `PERSONAL_ASSISTANT_PROMPT`, a system prompt that
  tells the LLM it is answering a call on Harshith's behalf: greet, ask who's
  calling, ask the purpose, take a message or callback if asked, wrap up
  politely on goodbye. Never invent facts, never pretend to be Harshith.
- Critically, the prompt forces **structured output**: the model must reply
  with a single JSON object `{"reply": ..., "intent": ..., "caller_name": ...}`
  — never bare text. This is requested via `llm.chat(..., json_mode=True)`,
  which sets Ollama's `"format": "json"`. One LLM call per turn produces both
  the spoken reply *and* the intent classification — no separate classifier
  call, so latency doesn't double.
- `intent` is one of the fixed set from `CLAUDE.md` §13 (`GREETING`,
  `MESSAGE`, `CALLBACK`, `END_CALL`, etc.) — `_parse_reply()` falls back to
  `UNKNOWN` and treats the raw text as the reply if the model ever returns
  malformed JSON, so a bad model output degrades gracefully instead of
  crashing the endpoint.
- State kept at module level in `agent.py` (in-memory, single ongoing call —
  will move to SQLite/per-call rows in Phase 8):
  - `conversation_history` — this call's message list, seeded with the
    system prompt.
  - `current_caller` — `{"name": ...}`, filled in once the model extracts a
    name from what the caller said.
  - `messages_taken` — every `MESSAGE` or `CALLBACK` intent appends a row
    here: `{caller_name, message, callback_required, created_at}` — shaped
    to match the `Messages` table planned for Phase 8, so persisting it
    later is a straight insert, not a redesign.
  - `call_summaries` — filled on `END_CALL`.
- **Actions** (`CLAUDE.md` §14), implemented as plain functions, no
  orchestration framework:
  - `take_message(caller, text, callback_required)` — appends to
    `messages_taken`. Used for both `MESSAGE` and `CALLBACK` intents (a
    callback request is just a message with `callback_required=True`).
  - `generate_summary(history)` — one extra LLM call (plain text, not JSON),
    only fired once per call, on `END_CALL`.
- **Call boundary**: on `END_CALL`, `handle_message()` generates the summary,
  then clears `conversation_history` back to just the system prompt and
  resets `current_caller` to `None`. This simulates hanging up — the next
  message starts a fresh "call" with no memory of the previous caller. There
  is no real telephony session yet, so this reset is what currently defines
  where one call ends and the next begins.

### `app/llm.py` — the brain

- Sends the full conversation history to Ollama's `/api/chat` endpoint.
- Model: `qwen3:8b` (read from `OLLAMA_MODEL` env var).
- `"think": False` is passed explicitly — `qwen3` is a hybrid "thinking" model
  that otherwise spends ~40s per reply generating an internal reasoning trace
  before answering. Disabling it brought reply time down to ~3-11s.
- On any request failure (Ollama not running, timeout, etc.) it returns a
  friendly fallback string instead of raising, so the API never 500s just
  because the LLM is unreachable.

### `app/stt.py` — the ears

- Wraps `faster_whisper.WhisperModel`, model size `base` (read from
  `WHISPER_MODEL` env var), running on CPU with `int8` quantization for speed.
- The model is loaded lazily on first use and cached in a module-level
  singleton (`_model`), so it's only loaded once per server process, not once
  per request — loading takes several seconds.
- `transcribe(audio_path)` returns the joined text of all detected segments.

### `app/tts.py` — the mouth

- Wraps `piper.PiperVoice`, using the `en_US-lessac-medium` voice model
  (path read from `PIPER_VOICE` env var, defaults to
  `data/voices/en_US-lessac-medium.onnx`).
- Same lazy-singleton pattern as STT — the voice model loads once and is
  reused.
- `synthesize(text, wav_path)` writes a WAV file to disk and returns the path.
- The voice model files are not committed to git (see `.gitignore`); they're
  downloaded once via `python -m piper.download_voices en_US-lessac-medium
  --download-dir data/voices` (documented in `README.md`).

### `app/main.py` — the router

Wires `agent`, `stt`, and `tts` into HTTP endpoints, and serves the frontend
as static files.

- `load_dotenv()` runs at import time so `OLLAMA_MODEL`, `OLLAMA_HOST`,
  `WHISPER_MODEL`, `PIPER_VOICE` are all picked up from `.env`.
- `/api/chat` is now a thin wrapper around `agent.handle_message()` — all the
  conversation/intent/action logic lives in `app/agent.py` (see above), not
  here. The response shape (`{"reply": ..., "intent": ...}`) is
  backward-compatible with the earlier generic-chat version — the frontend
  only reads `.reply`, so it needed no changes.

### `frontend/index.html` — the face

A single page with:
- A scrolling chat log (`#chat`).
- A text input + Send button (manual text chat).
- A 🎤 record button (voice chat).
- No build step, no framework — vanilla `fetch`, `MediaRecorder`, `Audio`.

---

## 5. API endpoints

| Method | Path | Request | Response | Purpose |
|---|---|---|---|---|
| GET | `/health` | — | `{"status": "ok"}` | Liveness check |
| POST | `/api/chat` | `{"message": "..."}` | `{"reply": "...", "intent": "..."}` | Runs one Personal Assistant turn via `agent.handle_message()` |
| GET | `/api/messages` | — | list of `{caller_name, message, callback_required, created_at}` | Every message/callback taken so far, across calls |
| POST | `/api/stt` | multipart form, field `audio` (audio file blob) | `{"text": "..."}` | Transcribe uploaded audio to text |
| POST | `/api/tts` | `{"text": "..."}` | `audio/wav` file bytes | Synthesize text to speech |
| GET | `/` and static paths | — | `frontend/index.html`, `style.css`, etc. | Serves the UI |

`/api/stt` and `/api/tts` are stateless and independent of each other and of
`/api/chat`. The frontend is what chains them together into a conversation
turn (see data flow below).

---

## 6. Data flow

### 6.1 Text chat (typed message)

```
Browser (type + Send)
   │  fetch POST /api/chat  { message }
   ▼
FastAPI /api/chat  -->  agent.handle_message(message)
   │  appends {role: user, content: message} to agent.conversation_history
   │  calls llm.chat(conversation_history, json_mode=True)
   ▼
app/llm.py --> POST http://localhost:11434/api/chat  (Ollama)
   │  model = qwen3:8b, think = false, format = json
   ▼
Ollama returns { message: { content: '{"reply": "...", "intent": "...", ...}' } }
   │
   ▼
agent._parse_reply() parses the JSON --> {reply, intent, caller_name}
   │  appends {role: assistant, content: reply} to conversation_history
   │  updates current_caller if a name was extracted
   │  if intent is MESSAGE/CALLBACK -> take_message(...)
   │  if intent is END_CALL -> generate_summary(...), reset conversation
   ▼
FastAPI returns { reply, intent }
   │
   ▼
Browser displays "AI: <reply>" and calls speak(reply)   (intent is ignored by the UI today)
```

### 6.2 Full voice turn (🎤 button) — the complete pipeline

This is the "first major milestone" from `CLAUDE.md` §10: a full spoken,
multi-turn conversation.

```
1. User clicks 🎤
   Browser: MediaRecorder captures mic audio (webm)

2. User clicks 🎤 again (stop)
   Browser: audio blob --> FormData --> fetch POST /api/stt
        ▼
   FastAPI /api/stt: saves upload to a temp file, calls stt.transcribe()
        ▼
   app/stt.py: faster-whisper decodes + transcribes --> text
        ▼
   FastAPI returns { text }
        ▼
   Browser: sendMessage(text)   <-- same function the typed-chat path uses

3. sendMessage(text)
   Browser: shows "You: <text>", fetch POST /api/chat { message: text }
        ▼
   [ same as section 6.1 above: FastAPI -> Ollama -> reply ]
        ▼
   Browser: shows "AI: <reply>", calls speak(reply)

4. speak(reply)
   Browser: fetch POST /api/tts { text: reply }
        ▼
   FastAPI /api/tts: calls tts.synthesize(reply, tmp_wav_path)
        ▼
   app/tts.py: Piper synthesizes speech --> WAV file on disk
        ▼
   FastAPI streams the WAV back as the response,
   then deletes the temp file via a BackgroundTask
        ▼
   Browser: builds a Blob, new Audio(...).play()  --> user hears the reply
```

So one spoken turn touches the backend three times (`/api/stt`, `/api/chat`,
`/api/tts`), all orchestrated by the frontend, not the backend — there's no
single "handle a voice turn" endpoint. This keeps each endpoint small,
independently testable, and reusable (e.g. `/api/chat` is also used by the
typed-text path).

### 6.3 Temp file handling

Both `/api/stt` (incoming audio) and `/api/tts` (outgoing audio) write to the
OS temp directory rather than `data/`, and clean up after themselves:
- `/api/stt` deletes the temp upload in a `finally` block right after
  transcribing.
- `/api/tts` can't delete the file before the response is sent (FastAPI
  streams it), so deletion is deferred via `BackgroundTasks`, which runs
  after the response has been fully sent to the client.

No audio is persisted to disk long-term yet — consistent with `CLAUDE.md`
§40 (avoid storing audio unless necessary).

---

## 7. Configuration

All config lives in `.env` (git-ignored; `.env.example` is the template):

| Variable | Default | Used by |
|---|---|---|
| `OLLAMA_MODEL` | `qwen3:8b` | `app/llm.py` |
| `OLLAMA_HOST` | `http://localhost:11434` | `app/llm.py` |
| `WHISPER_MODEL` | `base` (hardcoded default, not in `.env.example`) | `app/stt.py` |
| `PIPER_VOICE` | `data/voices/en_US-lessac-medium.onnx` (hardcoded default) | `app/tts.py` |

---

## 8. Known constraints / things to keep in mind

- **Conversation memory is global, not per-user.** There's one shared
  `conversation_history` list in `app/agent.py`, holding exactly one call at
  a time. It resets on `END_CALL`, but there's no way today to run two calls
  concurrently — fine for a single-user local demo, but will need real
  per-call/per-session scoping once telephony brings multiple simultaneous
  callers (Phase 10).
- **No persistence yet.** Restarting the server wipes conversation history,
  `messages_taken`, and `call_summaries`. Nothing is written to a database —
  that's Phase 8. `messages_taken` rows are already shaped to match the
  planned `Messages` table so that migration should be a straight insert.
- **Intent classification relies on the model returning well-formed JSON.**
  `_parse_reply()` has a fallback (treat the raw text as the reply, intent =
  `UNKNOWN`) if it doesn't, so the app won't crash — but a malformed response
  means that turn's intent-based action (taking a message, ending the call)
  silently doesn't fire. Worth watching if a different/smaller model is
  swapped in later, since JSON-following reliability varies by model.
- **Ollama's `qwen3:8b` "thinking" mode is disabled** for latency reasons.
  If the model is swapped for a non-hybrid model later, the `"think": False`
  field in `app/llm.py` is harmless (ignored by models that don't support it).
- **Whisper/Piper models are not committed to git** — a fresh clone needs to
  run `ollama pull qwen3:8b` and `python -m piper.download_voices ...` before
  the app fully works (see `README.md` Setup section).
- **Latency today:** ~3-11s per LLM reply, ~3-4s for STT/TTS each on a short
  clip. Within the "3-5s eventually" target range from `CLAUDE.md` §27 for
  the LLM step; STT+TTS add on top of that for a full voice turn. No
  optimization has been done yet — this is the "make it work" phase.

---

## 9. Status

See `README.md` for the up-to-date module checklist. As of this writing:
Phases 1-6 (project setup, LLM chat, STT, TTS, full voice pipeline, Personal
Assistant agent) are done and manually tested end-to-end, including the
exact "Rahul asking for Harshith" call flow from `CLAUDE.md` §11. Phase 7
(Sales Agent) is next.
