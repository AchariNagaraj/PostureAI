"""High‑level persistence service used by the FastAPI WebSocket.

Provides explicit session lifecycle functions that rely solely on database state.
"""

from typing import Dict, Any
import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from . import db, models, repositories

# ---------- Session lifecycle ----------

class ConflictError(Exception):
    """Raised when a request would create a conflicting active session."""

async def start_session(user_id: int | None = None, request_id: str | None = None) -> int:
    """Create a new ACTIVE session.

    If an ACTIVE session already exists for the user, raise ConflictError.
    """
    async with db.AsyncSessionLocal() as session:
        # Check for existing ACTIVE session first
        existing = await repositories.get_active_session(session, user_id=user_id)
        if existing:
            raise ConflictError("Active session already exists for this user")
        # No conflict – create new session
        new_session = await repositories.create_session(session, start_ts=time.time(), user_id=user_id)
        return new_session.id

async def resume_session(user_id: int, session_id: int) -> int:
    """Validate that the ACTIVE session belongs to the user and return its id."""
    async with db.AsyncSessionLocal() as session:
        s = await repositories.get_session_by_id(session, session_id, user_id=user_id)
        if not s:
            raise ValueError("Session not found or does not belong to user")
        if s.status != "ACTIVE":
            raise ValueError("Session is not ACTIVE")
        return s.id

async def close_session(user_id: int, session_id: int) -> None:
    """Mark the specified session as COMPLETED. Idempotent – second calls are no‑ops."""
    async with db.AsyncSessionLocal() as session:
        s = await repositories.get_session_by_id(session, session_id, user_id=user_id)
        if s and s.status != "COMPLETED":
            await repositories.finish_session(session, session_id, end_ts=time.time(), user_id=user_id)

async def persist_event(event_type: str, payload: Dict[str, Any], user_id: int | None = None, session_id: int | None = None) -> None:
    """Persist a monitoring event for an existing ACTIVE session.

    ``session_id`` must be supplied – the caller ensures the session is ACTIVE.
    """
    if session_id is None:
        raise ValueError("session_id must be provided to persist_event")
    async with db.AsyncSessionLocal() as session:
        try:
            if event_type == "POSTURE_UPDATE":
                metric = models.PostureMetric(
                    session_id=session_id,
                    user_id=user_id,
                    timestamp=payload["timestamp"],
                    posture=payload["posture"],
                    confidence=payload.get("confidence", 0.0),
                    risk_score=payload.get("risk_score", 0.0),
                    risk_level=payload.get("risk_level", "NORMAL"),
                    temporal_state=payload.get("temporal_state", "NORMAL"),
                    viewpoint=payload.get("viewpoint"),
                    tracking_state=payload.get("tracking_state"),
                    pose_valid=payload.get("pose_valid"),
                )
                await repositories.add_metric(session, metric)
            elif event_type == "ALERT":
                alert = models.Alert(
                    session_id=session_id,
                    user_id=user_id,
                    timestamp=payload["timestamp"],
                    posture=payload.get("posture", ""),
                    risk_score=payload.get("risk_score", 0.0),
                    risk_level=payload.get("risk_level", "ALERT"),
                    alert_type=payload.get("alert_type", "RISK_ALERT"),
                    message=payload.get("message"),
                    voice_message=payload.get("voice_message"),
                    viewpoint=payload.get("viewpoint"),
                    risk_state=payload.get("temporal_state"),
                )
                await repositories.add_alert(session, alert)
        except Exception as exc:
            print(f"[persistence] failed to store {event_type}: {exc}")
