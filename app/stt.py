import os

from faster_whisper import WhisperModel

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str) -> str:
    """Transcribe an audio file to text."""
    segments, _ = _get_model().transcribe(audio_path)
    return " ".join(segment.text.strip() for segment in segments).strip()
