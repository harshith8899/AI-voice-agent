import os
import tempfile

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from app import database as db
from app.agent import handle_message, handle_sales_message
from app.stt import transcribe
from app.tts import synthesize

db.init_db()

app = FastAPI(title="AI Voice Agent")


class ChatRequest(BaseModel):
    message: str


class TTSRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    return handle_message(req.message)


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


@app.post("/api/stt")
async def stt_endpoint(audio: UploadFile):
    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name
    try:
        text = transcribe(tmp_path)
    except Exception as e:
        print(f"[stt] transcription failed: {e}")
        text = ""
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
