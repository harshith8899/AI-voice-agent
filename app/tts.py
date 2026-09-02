import os
import wave

from piper import PiperVoice

DEFAULT_VOICE = os.path.join(
    os.path.dirname(__file__), "..", "data", "voices", "en_US-lessac-medium.onnx"
)
VOICE_MODEL = os.getenv("PIPER_VOICE", DEFAULT_VOICE)

_voice = None


def _get_voice():
    global _voice
    if _voice is None:
        model_path = VOICE_MODEL
        if not os.path.isabs(model_path) and not os.path.exists(model_path):
            model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", model_path))
        _voice = PiperVoice.load(model_path)
    return _voice


def synthesize(text: str, wav_path: str) -> str:
    """Synthesize text to speech and write it to wav_path."""
    voice = _get_voice()
    with wave.open(wav_path, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)
    return wav_path
