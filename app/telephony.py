import os
import re
import tempfile
import time
import uuid
from xml.sax.saxutils import escape

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

_AUDIO_FILENAME_RE = re.compile(r"^[0-9a-f]{32}\.wav$")

from app.agent import handle_message, start_call
from app.stt import transcribe
from app.tts import synthesize

router = APIRouter()

AUDIO_DIR = "data/telephony_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

REPROMPT_TEXT = "Sorry, I didn't catch that. Could you repeat?"


def _cleanup_old_audio(max_age_seconds: int = 300) -> None:
    now = time.time()
    for name in os.listdir(AUDIO_DIR):
        path = os.path.join(AUDIO_DIR, name)
        try:
            if now - os.path.getmtime(path) > max_age_seconds:
                os.remove(path)
        except OSError:
            pass


def _save_reply_audio(text: str) -> str:
    filename = f"{uuid.uuid4().hex}.wav"
    synthesize(text, os.path.join(AUDIO_DIR, filename))
    return filename


def _xml(body: str) -> Response:
    return Response(
        content=f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>',
        media_type="application/xml",
    )


def _play_and_record(base: str, filename: str) -> Response:
    play = f'<Play>{escape(base)}/api/telephony/audio/{filename}</Play>'
    record = (
        f'<Record callbackUrl="{escape(base)}/api/telephony/recording" '
        'method="POST" callbackMethod="POST" fileFormat="wav" maxLength="30" timeout="5"/>'
    )
    return _xml(play + record)


@router.post("/api/telephony/answer")
async def telephony_answer(request: Request):
    _cleanup_old_audio()
    form = await request.form()
    phone = form.get("From")

    greeting = start_call(phone=phone)
    filename = _save_reply_audio(greeting)
    return _play_and_record(str(request.base_url).rstrip("/"), filename)


@router.post("/api/telephony/recording")
async def telephony_recording(request: Request):
    _cleanup_old_audio()
    form = await request.form()
    recording_url = form.get("RecordFile")
    base = str(request.base_url).rstrip("/")

    user_text = ""
    if recording_url:
        try:
            resp = requests.get(recording_url, timeout=20)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name
            try:
                user_text = transcribe(tmp_path)
            finally:
                os.remove(tmp_path)
        except Exception as e:
            print(f"[telephony] failed to fetch/transcribe recording: {e}")

    if not user_text.strip():
        filename = _save_reply_audio(REPROMPT_TEXT)
        return _play_and_record(base, filename)

    result = handle_message(user_text)
    filename = _save_reply_audio(result["reply"])

    if result["intent"] == "END_CALL":
        play = f'<Play>{escape(base)}/api/telephony/audio/{filename}</Play>'
        return _xml(play + "<Hangup/>")

    return _play_and_record(base, filename)


@router.get("/api/telephony/audio/{filename}")
def telephony_audio(filename: str):
    if not _AUDIO_FILENAME_RE.match(filename):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(os.path.join(AUDIO_DIR, filename), media_type="audio/wav")
