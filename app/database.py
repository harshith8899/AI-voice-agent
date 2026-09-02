import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caller_name TEXT,
    phone TEXT,
    agent_type TEXT NOT NULL,
    start_time TEXT NOT NULL,
    duration REAL,
    intent TEXT,
    summary TEXT,
    status TEXT NOT NULL DEFAULT 'in_progress'
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL REFERENCES calls(id),
    speaker TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL REFERENCES calls(id),
    caller_name TEXT,
    message TEXT NOT NULL,
    callback_required INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL REFERENCES calls(id),
    name TEXT,
    phone TEXT,
    interest TEXT,
    score INTEGER NOT NULL,
    classification TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with _connect() as conn:
        conn.executescript(SCHEMA)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_call(agent_type: str, caller_name: str | None = None) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO calls (caller_name, agent_type, start_time, status) VALUES (?, ?, ?, 'in_progress')",
            (caller_name, agent_type, _now()),
        )
        return cur.lastrowid


def update_call_caller(call_id: int, caller_name: str | None = None, phone: str | None = None) -> None:
    with _connect() as conn:
        if caller_name is not None:
            conn.execute("UPDATE calls SET caller_name = ? WHERE id = ?", (caller_name, call_id))
        if phone is not None:
            conn.execute("UPDATE calls SET phone = ? WHERE id = ?", (phone, call_id))


def update_call_activity(
    call_id: int,
    intent: str | None = None,
    caller_name: str | None = None,
    phone: str | None = None,
) -> None:
    """Update call duration, intent, caller name, and phone dynamically on every turn."""
    with _connect() as conn:
        row = conn.execute("SELECT start_time FROM calls WHERE id = ?", (call_id,)).fetchone()
        duration = None
        if row and row["start_time"]:
            try:
                start = datetime.fromisoformat(row["start_time"])
                duration = round((datetime.now(timezone.utc) - start).total_seconds(), 1)
            except Exception:
                duration = None

        updates = []
        params = []
        if intent is not None and intent != "UNKNOWN":
            updates.append("intent = ?")
            params.append(intent)
        elif intent is not None:
            updates.append("intent = COALESCE(intent, ?)")
            params.append(intent)
        if caller_name is not None:
            updates.append("caller_name = ?")
            params.append(caller_name)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        if duration is not None:
            updates.append("duration = ?")
            params.append(duration)

        if updates:
            params.append(call_id)
            sql = f"UPDATE calls SET {', '.join(updates)} WHERE id = ?"
            conn.execute(sql, tuple(params))


def end_call(call_id: int, intent: str | None = None, summary: str | None = None) -> None:
    with _connect() as conn:
        row = conn.execute("SELECT start_time, intent, summary FROM calls WHERE id = ?", (call_id,)).fetchone()
        duration = None
        final_intent = intent or (row["intent"] if row and row["intent"] else "COMPLETED")
        final_summary = summary or (row["summary"] if row and row["summary"] else None)
        if row and row["start_time"]:
            try:
                start = datetime.fromisoformat(row["start_time"])
                duration = round((datetime.now(timezone.utc) - start).total_seconds(), 1)
            except Exception:
                duration = None
        conn.execute(
            "UPDATE calls SET intent = ?, summary = ?, status = 'completed', duration = ? WHERE id = ?",
            (final_intent, final_summary, duration, call_id),
        )


def add_conversation(call_id: int, speaker: str, message: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO conversations (call_id, speaker, message, timestamp) VALUES (?, ?, ?, ?)",
            (call_id, speaker, message, _now()),
        )


def add_message(call_id: int, caller_name: str | None, message: str, callback_required: bool) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (call_id, caller_name, message, callback_required, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (call_id, caller_name, message, int(callback_required), _now()),
        )


def add_lead(
    call_id: int,
    name: str | None,
    phone: str | None,
    interest: str | None,
    score: int,
    classification: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO leads (call_id, name, phone, interest, score, classification, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (call_id, name, phone, interest, score, classification, _now()),
        )


def get_calls() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM calls ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_call(call_id: int) -> dict | None:
    with _connect() as conn:
        call = conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
        if not call:
            return None
        transcript = conn.execute(
            "SELECT speaker, message, timestamp FROM conversations WHERE call_id = ? ORDER BY id", (call_id,)
        ).fetchall()
        result = dict(call)
        result["transcript"] = [dict(r) for r in transcript]
        return result


def get_messages() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
        messages = [dict(r) for r in rows]
        for m in messages:
            m["callback_required"] = bool(m["callback_required"])
        return messages


def get_leads() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_dashboard_metrics() -> dict:
    with _connect() as conn:
        total_calls = conn.execute("SELECT COUNT(*) FROM calls").fetchone()[0] or 0
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] or 0
        total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0] or 0
        booked_actions = total_messages + total_leads
        avg_duration_row = conn.execute(
            "SELECT AVG(duration) FROM calls WHERE duration IS NOT NULL"
        ).fetchone()[0]
        avg_duration = round(float(avg_duration_row), 1) if avg_duration_row is not None else 0.0

        return {
            "total_calls": total_calls,
            "booked_actions": booked_actions,
            "total_actions": booked_actions,
            "total_messages": total_messages,
            "total_leads": total_leads,
            "avg_duration": avg_duration,
        }


def get_call_logs(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, caller_name, phone, agent_type, start_time, duration, intent, summary, status "
            "FROM calls ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        logs = []
        for r in rows:
            logs.append(
                {
                    "call_id": r["id"],
                    "id": r["id"],
                    "caller_name": r["caller_name"] or "Unknown",
                    "caller_phone": r["phone"] or "-",
                    "phone": r["phone"] or "-",
                    "agent_type": r["agent_type"],
                    "call_status": r["status"],
                    "status": r["status"],
                    "start_time": r["start_time"],
                    "created_at": r["start_time"],
                    "duration": round(r["duration"], 1) if r["duration"] is not None else None,
                    "intent": r["intent"] or "-",
                    "summary": r["summary"] or "",
                }
            )
        return logs


def get_call_transcript(call_id: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT speaker, message, timestamp FROM conversations WHERE call_id = ? ORDER BY id",
            (call_id,),
        ).fetchall()
        return [dict(r) for r in rows]

