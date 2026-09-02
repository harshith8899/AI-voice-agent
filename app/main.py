import os
import tempfile

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# pyrefly: ignore [missing-import]
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

from app import database as db
from app.agent import handle_message, handle_sales_message, reset_agent
from app.stt import transcribe
from app.tts import synthesize

db.init_db()

app = FastAPI(title="AI Voice Agent")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


class ChatRequest(BaseModel):
    message: str


class ResetRequest(BaseModel):
    agent: str = "all"


class TTSRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    return handle_message(req.message)


@app.post("/api/chat/reset")
def reset_chat_endpoint(req: ResetRequest | None = None):
    agent_type = req.agent if req and req.agent else "all"
    return reset_agent(agent_type)


@app.get("/api/messages")
def messages_endpoint():
    return db.get_messages()


@app.post("/api/sales/chat")
def sales_chat_endpoint(req: ChatRequest):
    return handle_sales_message(req.message)


@app.get("/api/leads")
def leads_endpoint():
    return db.get_leads()


@app.get("/api/calls")
def calls_endpoint():
    return db.get_calls()


@app.get("/api/calls/{call_id}")
def call_detail_endpoint(call_id: int):
    call = db.get_call(call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@app.get("/api/dashboard/metrics")
def dashboard_metrics_endpoint():
    return db.get_dashboard_metrics()


@app.get("/api/dashboard/calls")
def dashboard_calls_endpoint(limit: int = 50):
    return db.get_call_logs(limit=limit)


@app.get("/api/dashboard/calls/{call_id}/transcript")
def dashboard_call_transcript_endpoint(call_id: int):
    call = db.get_call(call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")
    return db.get_call_transcript(call_id)


@app.post("/api/stt")
async def stt_endpoint(audio: UploadFile):
    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name
    try:
        text = transcribe(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return {"text": text}


@app.post("/api/tts")
def tts_endpoint(req: TTSRequest, background_tasks: BackgroundTasks):
    tmp_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    synthesize(req.text, tmp_path)
    background_tasks.add_task(lambda p: os.remove(p) if os.path.exists(p) else None, tmp_path)
    return FileResponse(tmp_path, media_type="audio/wav")


if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
