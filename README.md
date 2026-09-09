# AI Voice Agent

College project: a simple AI voice agent that can act as a **Personal Assistant** (answer calls, take messages, callbacks) and a **Sales Agent** (qualify leads), eventually connected to a real phone line.

Full spec: [`AI Voice Agent for Phone Call Automation.md`](./AI%20Voice%20Agent%20for%20Phone%20Call%20Automation.md)
Development rules: [`CLAUDE.md`](./CLAUDE.md)

## Stack

Python + FastAPI · Whisper (STT) · Ollama (LLM) · Piper (TTS) · SQLite · HTML/CSS/JS

## Project Structure

```
app/            FastAPI backend (main.py, agent.py, stt.py, llm.py, tts.py, database.py, prompts.py)
frontend/       Plain HTML/CSS/JS UI
data/           SQLite database (not committed)
tests/          Tests
requirements.txt
.env.example    Copy to .env and fill in values (.env is git-ignored)
```

## Setup

```bash
# use Python 3.12 (3.14 is too new for some ML packages used later)
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
```

Requires [Ollama](https://ollama.com) running locally with the model in `.env` pulled (`ollama pull qwen3:8b`).

Download the Piper voice (not committed to git):

```bash
python -m piper.download_voices en_US-lessac-medium --download-dir data/voices
```

## Run

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` for the frontend, `http://localhost:8000/health` for the health check.

## API

```
GET  /health           Health check
POST /api/chat          Personal Assistant, one turn   {"message": "..."}
POST /api/sales/chat    Sales Agent, one turn           {"message": "..."}
POST /api/stt            Transcribe uploaded audio -> text
POST /api/tts            Synthesize text -> wav audio
GET  /api/calls          List all calls
GET  /api/calls/{id}     Call detail + full transcript
GET  /api/messages       Messages taken by the Personal Assistant
GET  /api/leads          Leads captured by the Sales Agent

POST /api/telephony/answer      Vobiz answer_url webhook (inbound call -> greeting XML)
POST /api/telephony/recording   Vobiz recording callback (caller audio -> reply XML)
GET  /api/telephony/audio/{f}   Serves generated reply audio back to Vobiz
```

The frontend has an Agent dropdown (Personal Assistant / Sales Agent) that switches which chat endpoint is used.

## Telephony (Vobiz)

Real phone calls route to the Personal Assistant using Vobiz's Record/Play XML flow (turn-based,
no WebSocket streaming): Vobiz posts call events to our webhooks, we run the same
`transcribe() -> handle_message() -> synthesize()` pipeline used everywhere else, and respond
with Voice XML telling Vobiz what to play/record next.

1. Sign up at [console.vobiz.ai](https://console.vobiz.ai), buy a phone number.
2. Run `uvicorn app.main:app --reload` locally, then expose it: `ngrok http 8000`.
3. In the Vobiz console, create an XML Application with:
   - Answer URL: `https://<your-ngrok-domain>/api/telephony/answer`
   - Method: `POST`
4. Attach your purchased number to that Application.
5. Call the number — you should hear the Personal Assistant greeting and be able to hold a
   multi-turn conversation.

Currently supports **one active call at a time** (matches the browser demo's single-conversation
state) and inbound calls to the Personal Assistant only. Outbound/Sales calling and concurrent
calls are not implemented — not needed for the MVP demo.

## Status

| Module | Status |
|---|---|
| 1. Project setup (FastAPI skeleton) | ✅ Done |
| 2. LLM text chat (Ollama) | ✅ Done |
| 3. Speech-to-Text (Whisper) | ✅ Done |
| 4. Text-to-Speech (Piper) | ✅ Done |
| 5. Full voice pipeline | ✅ Done |
| 6. Personal Assistant agent | ✅ Done |
| 7. Sales Agent | ✅ Done |
| 8. Database (calls/messages/leads) | ✅ Done |
| 9. Dashboard | ✅ Done |
| 10. Telephony (real phone calls) | ✅ Inbound calls to Personal Assistant via Vobiz |

## Development principle

**Simple > Complex. Working > Perfect.** See `CLAUDE.md` for full rules — no microservices, no unnecessary dependencies, smallest change that works.
