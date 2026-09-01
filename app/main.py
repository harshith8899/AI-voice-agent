from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from app.llm import chat

app = FastAPI(title="AI Voice Agent")

SYSTEM_PROMPT = (
    "You are a helpful voice assistant. Keep replies short (1-3 sentences), "
    "natural, and voice-friendly. Ask one question at a time."
)
conversation_history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    conversation_history.append({"role": "user", "content": req.message})
    reply = chat(conversation_history)
    conversation_history.append({"role": "assistant", "content": reply})
    return {"reply": reply}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
