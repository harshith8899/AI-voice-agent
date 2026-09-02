import os
import requests
from dotenv import load_dotenv

load_dotenv()


def _get_available_model(host: str) -> str | None:
    """Fetch the first available model from Ollama if configured model is missing."""
    try:
        res = requests.get(f"{host.rstrip('/')}/api/tags", timeout=5)
        if res.status_code == 200:
            models = res.json().get("models", [])
            if models:
                return models[0].get("name")
    except Exception:
        pass
    return None


def chat(messages: list[dict], json_mode: bool = False) -> str:
    """Send conversation history to Ollama and return the assistant's reply text."""
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"

    try:
        response = requests.post(
            f"{host.rstrip('/')}/api/chat",
            json=payload,
            timeout=60,
        )
        if response.status_code == 404:
            # Configured model might have :latest or differ, try auto-detecting installed model
            fallback_model = _get_available_model(host)
            if fallback_model and fallback_model != model:
                payload["model"] = fallback_model
                response = requests.post(
                    f"{host.rstrip('/')}/api/chat",
                    json=payload,
                    timeout=60,
                )

        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.RequestException as e:
        print(f"[llm] Ollama request failed (host={host}, model={model}): {e}")
        return "Sorry, I'm having trouble processing that right now."
