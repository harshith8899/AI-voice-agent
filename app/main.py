import os
import tempfile

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from app.llm import chat
from app.stt import transcribe
from app.tts import synthesize

app = FastAPI(title="AI Voice Agent")

SYSTEM_PROMPT = (
    "You are a helpful voice assistant. Keep replies short (1-3 sentences), "
    "natural, and voice-friendly. Ask one question at a time."
)
conversation_history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]


class ChatRequest(BaseModel):
    message: str


class TTSRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    conversation_history.append({"role": "user", "content": req.message})
    reply = chat(conversation_history)
    conversation_history.append({"role": "assistant", "content": reply})
    return {"reply": reply}


@app.post("/api/stt")
async def stt_endpoint(audio: UploadFile):
    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name
    try:
        text = transcribe(tmp_path)
    finally:
        os.remove(tmp_path)
    return {"text": text}


@app.post("/api/tts")
def tts_endpoint(req: TTSRequest, background_tasks: BackgroundTasks):
    tmp_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    synthesize(req.text, tmp_path)
    background_tasks.add_task(os.remove, tmp_path)
    return FileResponse(tmp_path, media_type="audio/wav")


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
