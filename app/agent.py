import json
from datetime import datetime, timezone

from app.llm import chat
from app.prompts import PERSONAL_ASSISTANT_PROMPT

INTENTS = {
    "GREETING",
    "GENERAL_QUERY",
    "PRODUCT_QUERY",
    "PRICING_QUERY",
    "MESSAGE",
    "CALLBACK",
    "INTERESTED",
    "NOT_INTERESTED",
    "HUMAN_REQUEST",
    "END_CALL",
    "UNKNOWN",
}

# In-memory stores (will move to SQLite in Phase 8).
messages_taken: list[dict] = []
call_summaries: list[str] = []

conversation_history: list[dict] = [{"role": "system", "content": PERSONAL_ASSISTANT_PROMPT}]
current_caller: dict = {"name": None}


def take_message(caller: str, text: str, callback_required: bool) -> None:
    messages_taken.append(
        {
            "caller_name": caller,
            "message": text,
            "callback_required": callback_required,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def generate_summary(history: list[dict]) -> str:
    prompt = history + [
        {
            "role": "user",
            "content": (
                "Summarize this call in 3-4 short lines: who called, why, "
                "and any message or callback requested. Plain text, no JSON."
            ),
        }
    ]
    return chat(prompt)


def _parse_reply(raw: str) -> dict:
    try:
        data = json.loads(raw)
        reply = str(data.get("reply", "")).strip()
        intent = str(data.get("intent", "UNKNOWN")).strip().upper()
        caller_name = data.get("caller_name")
    except (json.JSONDecodeError, AttributeError):
        reply, intent, caller_name = raw.strip(), "UNKNOWN", None

    if intent not in INTENTS:
        intent = "UNKNOWN"
    if not reply:
        reply = "Sorry, could you repeat that?"

    return {"reply": reply, "intent": intent, "caller_name": caller_name}


def handle_message(user_message: str) -> dict:
    """Run one turn of the personal assistant and update module-level state."""
    conversation_history.append({"role": "user", "content": user_message})
    raw = chat(conversation_history, json_mode=True)
    result = _parse_reply(raw)
    conversation_history.append({"role": "assistant", "content": result["reply"]})

    if result["caller_name"]:
        current_caller["name"] = result["caller_name"]
    caller = current_caller["name"] or "Unknown caller"

    if result["intent"] == "MESSAGE":
        take_message(caller, user_message, callback_required=False)
    elif result["intent"] == "CALLBACK":
        take_message(caller, user_message, callback_required=True)
    elif result["intent"] == "END_CALL":
        call_summaries.append(generate_summary(conversation_history))
        conversation_history.clear()
        conversation_history.append({"role": "system", "content": PERSONAL_ASSISTANT_PROMPT})
        current_caller["name"] = None

    return {"reply": result["reply"], "intent": result["intent"]}
