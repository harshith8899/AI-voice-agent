import json

from app import database as db
from app.llm import chat
from app.prompts import PERSONAL_ASSISTANT_PROMPT, SALES_AGENT_PROMPT

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

conversation_history: list[dict] = [{"role": "system", "content": PERSONAL_ASSISTANT_PROMPT}]
current_caller: dict = {"name": None}
current_call: dict = {"id": None}


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


def _clean_json_str(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return cleaned


def _parse_reply(raw: str) -> dict:
    try:
        data = json.loads(_clean_json_str(raw))
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
    if current_call["id"] is None:
        current_call["id"] = db.create_call(agent_type="personal_assistant")
    call_id = current_call["id"]

    conversation_history.append({"role": "user", "content": user_message})
    db.add_conversation(call_id, "user", user_message)

    raw = chat(conversation_history, json_mode=True)
    result = _parse_reply(raw)
    conversation_history.append({"role": "assistant", "content": result["reply"]})
    db.add_conversation(call_id, "assistant", result["reply"])

    if result["caller_name"]:
        current_caller["name"] = result["caller_name"]
    caller = current_caller["name"] or "Unknown caller"

    # Always update call duration, intent, and caller name on every turn
    db.update_call_activity(
        call_id,
        intent=result["intent"],
        caller_name=result["caller_name"],
    )

    if result["intent"] == "MESSAGE":
        db.add_message(call_id, caller, user_message, callback_required=False)
    elif result["intent"] == "CALLBACK":
        db.add_message(call_id, caller, user_message, callback_required=True)
    elif result["intent"] == "END_CALL":
        summary = generate_summary(conversation_history)
        db.end_call(call_id, intent="END_CALL", summary=summary)
        conversation_history.clear()
        conversation_history.append({"role": "system", "content": PERSONAL_ASSISTANT_PROMPT})
        current_caller["name"] = None
        current_call["id"] = None

    return {"reply": result["reply"], "intent": result["intent"], "call_id": call_id}


# ---------------------------------------------------------------------------
# Sales Agent
# ---------------------------------------------------------------------------

sales_history: list[dict] = [{"role": "system", "content": SALES_AGENT_PROMPT}]
current_lead: dict = {"name": None, "phone": None, "interest": None}
current_sales_call: dict = {"id": None}


def score_lead(interest: str | None, phone: str | None, name: str | None) -> tuple[int, str]:
    """Simple rule-based lead score (see CLAUDE.md section 18)."""
    score = 0
    if interest:
        score += 30  # expressed interest
        score += 30  # treated as purchase intent signal
    if phone:
        score += 20  # gave contact info -> budget/commitment proxy
    if name and interest:
        score += 20  # relevance: known person with a stated interest

    if score >= 80:
        classification = "HOT"
    elif score >= 60:
        classification = "WARM"
    elif score >= 40:
        classification = "COLD"
    else:
        classification = "LOW"
    return score, classification


def create_lead(call_id: int) -> None:
    score, classification = score_lead(
        current_lead["interest"], current_lead["phone"], current_lead["name"]
    )
    db.add_lead(
        call_id,
        current_lead["name"],
        current_lead["phone"],
        current_lead["interest"],
        score,
        classification,
    )


def _parse_sales_reply(raw: str) -> dict:
    try:
        data = json.loads(_clean_json_str(raw))
        reply = str(data.get("reply", "")).strip()
        intent = str(data.get("intent", "UNKNOWN")).strip().upper()
        caller_name = data.get("caller_name")
        phone = data.get("phone")
        interest = data.get("interest")
    except (json.JSONDecodeError, AttributeError):
        reply, intent, caller_name, phone, interest = raw.strip(), "UNKNOWN", None, None, None

    if intent not in INTENTS:
        intent = "UNKNOWN"
    if not reply:
        reply = "Sorry, could you repeat that?"

    return {
        "reply": reply,
        "intent": intent,
        "caller_name": caller_name,
        "phone": phone,
        "interest": interest,
    }


def handle_sales_message(user_message: str) -> dict:
    """Run one turn of the sales agent and update module-level state."""
    if current_sales_call["id"] is None:
        current_sales_call["id"] = db.create_call(agent_type="sales")
    call_id = current_sales_call["id"]

    sales_history.append({"role": "user", "content": user_message})
    db.add_conversation(call_id, "user", user_message)

    raw = chat(sales_history, json_mode=True)
    result = _parse_sales_reply(raw)
    sales_history.append({"role": "assistant", "content": result["reply"]})
    db.add_conversation(call_id, "assistant", result["reply"])

    if result["caller_name"]:
        current_lead["name"] = result["caller_name"]
    if result["phone"]:
        current_lead["phone"] = result["phone"]
    if result["interest"]:
        current_lead["interest"] = result["interest"]

    # Always update call duration, intent, caller name, and phone on every turn
    db.update_call_activity(
        call_id,
        intent=result["intent"],
        caller_name=result["caller_name"],
        phone=result["phone"],
    )

    if result["intent"] == "END_CALL":
        create_lead(call_id)
        summary = generate_summary(sales_history)
        db.end_call(call_id, intent="END_CALL", summary=summary)
        sales_history.clear()
        sales_history.append({"role": "system", "content": SALES_AGENT_PROMPT})
        current_lead["name"] = None
        current_lead["phone"] = None
        current_lead["interest"] = None
        current_sales_call["id"] = None

    return {"reply": result["reply"], "intent": result["intent"], "call_id": call_id}


# ---------------------------------------------------------------------------
# Session Reset Helpers
# ---------------------------------------------------------------------------


def reset_personal_assistant() -> dict:
    global current_call, current_caller, conversation_history
    if current_call["id"] is not None:
        call_id = current_call["id"]
        summary = None
        if len(conversation_history) > 1:
            try:
                summary = generate_summary(conversation_history)
            except Exception:
                summary = "Call completed."
        db.end_call(call_id, intent="COMPLETED", summary=summary)

    current_caller["name"] = None
    current_call["id"] = None
    conversation_history = [{"role": "system", "content": PERSONAL_ASSISTANT_PROMPT}]
    return {"status": "ok", "message": "Personal assistant reset"}


def reset_sales_agent() -> dict:
    global current_sales_call, current_lead, sales_history
    if current_sales_call["id"] is not None:
        call_id = current_sales_call["id"]
        if current_lead["name"] or current_lead["phone"] or current_lead["interest"]:
            create_lead(call_id)
        summary = None
        if len(sales_history) > 1:
            try:
                summary = generate_summary(sales_history)
            except Exception:
                summary = "Sales call completed."
        db.end_call(call_id, intent="COMPLETED", summary=summary)

    current_lead["name"] = None
    current_lead["phone"] = None
    current_lead["interest"] = None
    current_sales_call["id"] = None
    sales_history = [{"role": "system", "content": SALES_AGENT_PROMPT}]
    return {"status": "ok", "message": "Sales agent reset"}


def reset_agent(agent_type: str = "all") -> dict:
    if agent_type in ("assistant", "personal_assistant"):
        return reset_personal_assistant()
    elif agent_type in ("sales", "sales_agent"):
        return reset_sales_agent()
    else:
        reset_personal_assistant()
        reset_sales_agent()
        return {"status": "ok", "message": "All agents reset"}
