import os
import wave

from piper import PiperVoice

VOICE_MODEL = os.getenv("PIPER_VOICE", "data/voices/en_US-lessac-medium.onnx")

_voice = None


def _get_voice():
    global _voice
    if _voice is None:
        _voice = PiperVoice.load(VOICE_MODEL)
    return _voice


def synthesize(text: str, wav_path: str) -> str:
    """Synthesize text to speech and write it to wav_path."""
    voice = _get_voice()
    with wave.open(wav_path, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)
    return wav_path
