import os

import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


def chat(messages: list[dict]) -> str:
    """Send conversation history to Ollama and return the assistant's reply text."""
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "think": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.RequestException as e:
        print(f"[llm] Ollama request failed: {e}")
        return "Sorry, I'm having trouble processing that right now."
