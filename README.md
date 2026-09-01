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

## Status

| Module | Status |
|---|---|
| 1. Project setup (FastAPI skeleton) | ✅ Done |
| 2. LLM text chat (Ollama) | ✅ Done |
| 3. Speech-to-Text (Whisper) | ✅ Done |
| 4. Text-to-Speech (Piper) | ✅ Done |
| 5. Full voice pipeline | ✅ Done |
| 6. Personal Assistant agent | ✅ Done |
| 7. Sales Agent | ⬜ Next |
| 8. Database (calls/messages/leads) | ⬜ |
| 9. Dashboard | ⬜ |
| 10. Telephony (real phone calls) | ⬜ |

## Development principle

**Simple > Complex. Working > Perfect.** See `CLAUDE.md` for full rules — no microservices, no unnecessary dependencies, smallest change that works.
