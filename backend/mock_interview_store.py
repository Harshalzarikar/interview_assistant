"""File-backed store for mock interview sessions (transcript + analysis)."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_DATA_DIR = Path(__file__).parent / "data"
_DATA_FILE = _DATA_DIR / "mock_interviews.json"
_lock = threading.Lock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_all() -> dict[str, dict[str, Any]]:
    if not _DATA_FILE.exists():
        return {}
    try:
        with _DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(sessions: dict[str, dict[str, Any]]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)


def create_session(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    record = {
        "session_id": session_id,
        "status": "pending",
        "created_at": _utc_now_iso(),
        "completed_at": None,
        "transcript": [],
        "analysis": None,
        **payload,
    }
    with _lock:
        sessions = _load_all()
        sessions[session_id] = record
        _save_all(sessions)
    return record


def get_session(session_id: str) -> Optional[dict[str, Any]]:
    with _lock:
        return _load_all().get(session_id)


def update_session(session_id: str, **updates: Any) -> Optional[dict[str, Any]]:
    with _lock:
        sessions = _load_all()
        record = sessions.get(session_id)
        if not record:
            return None
        record.update(updates)
        sessions[session_id] = record
        _save_all(sessions)
        return record


def complete_session(
    session_id: str, transcript: list, analysis: Optional[dict[str, Any]] = None
) -> Optional[dict[str, Any]]:
    return update_session(
        session_id,
        status="completed",
        transcript=transcript,
        analysis=analysis,
        completed_at=_utc_now_iso(),
    )
