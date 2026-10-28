# ml/persistence/service.py
"""High‑level persistence service used by the FastAPI WebSocket.

The service receives the *already constructed* payload that will be sent to the
client. It decides whether to store a regular ``POSTURE_UPDATE`` as a
``PostureMetric`` or an ``ALERT`` as an ``Alert``. It also ensures a monitoring
``Session`` exists – the first call creates a session (using the timestamp of
the first payload) and subsequent calls reuse that session.

Failure to persist must **not** interrupt the WebSocket stream. Errors are
logged with ``print`` (simple for this phase) and then ignored.
"""

import asyncio
import time
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from . import db, models, repositories

# Global in‑memory reference to the current session id.
_current_session_id: int | None = None

async def _get_or_create_session(db_session: AsyncSession, timestamp: float, user_id: int | None = None) -> int:
    """Return the id of the active session, creating one if needed."""
    global _current_session_id
    if _current_session_id is None:
        session = await repositories.create_session(db_session, start_ts=timestamp, user_id=user_id)
        _current_session_id = session.id
    return _current_session_id

async def close_session(db_session: AsyncSession | None = None, end_timestamp: float | None = None, user_id: int | None = None):
    """Mark the current session as completed."""
    global _current_session_id
    if _current_session_id is None:
        return
    
    if db_session is None:
        async with db.AsyncSessionLocal() as session:
            await repositories.finish_session(session, _current_session_id, end_ts=end_timestamp or time.time(), user_id=user_id)
    else:
        await repositories.finish_session(db_session, _current_session_id, end_ts=end_timestamp or time.time(), user_id=user_id)
        
    _current_session_id = None

async def persist_event(event_type: str, payload: Dict[str, Any], user_id: int | None = None):
    """Persist a monitoring event."""
    async with db.AsyncSessionLocal() as session:
        try:
            # Ensure a session exists – use the event timestamp as start time.
            session_id = await _get_or_create_session(session, payload.get("timestamp", time.time()), user_id=user_id)

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

