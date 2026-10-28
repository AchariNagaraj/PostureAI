# ml/persistence/repositories.py
"""CRUD‑style helpers used by the persistence service.

All functions are async and receive an ``AsyncSession`` instance.
"""

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from . import models

# ---------- Session handling ----------
async def create_session(db: AsyncSession, start_ts: float, user_id: int | None = None) -> models.Session:
    # Auto-complete any existing active sessions for this user before launching new session
    stmt = select(models.Session).where(models.Session.status == "ACTIVE")
    if user_id is not None:
        stmt = stmt.where(models.Session.user_id == user_id)
    active_sessions = (await db.execute(stmt)).scalars().all()
    for s in active_sessions:
        s.status = "COMPLETED"
        if not s.end_timestamp:
            s.end_timestamp = start_ts
    session = models.Session(start_timestamp=start_ts, user_id=user_id, status="ACTIVE")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def finish_session(db: AsyncSession, session_id: int, end_ts: float, user_id: int | None = None) -> models.Session | None:
    stmt = select(models.Session).where(models.Session.id == session_id)
    if user_id is not None:
        stmt = stmt.where(models.Session.user_id == user_id)
    result = await db.execute(stmt)
    session = result.scalars().first()
    if session:
        session.end_timestamp = end_ts
        session.status = "COMPLETED"
        await db.commit()
        await db.refresh(session)
    return session

# ---------- PostureMetric ----------
async def add_metric(db: AsyncSession, metric: models.PostureMetric) -> models.PostureMetric:
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric

# ---------- Alert ----------
async def add_alert(db: AsyncSession, alert: models.Alert) -> models.Alert:
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert

# ---------- UserSetting ----------
async def set_setting(db: AsyncSession, key: str, value: str, user_id: int | None = None):
    stmt = select(models.UserSetting).where(models.UserSetting.key == key)
    if user_id is not None:
        stmt = stmt.where(models.UserSetting.user_id == user_id)
    result = await db.execute(stmt)
    setting = result.scalars().first()
    if setting:
        setting.value = value
    else:
        setting = models.UserSetting(key=key, value=value, user_id=user_id)
        db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return setting

# ---------- Analytics Query Helpers ----------
async def get_all_sessions(db: AsyncSession, user_id: int | None = None, limit: int = 50, offset: int = 0):
    stmt = select(models.Session)
    if user_id is not None:
        stmt = stmt.where(models.Session.user_id == user_id)
    stmt = stmt.order_by(models.Session.id.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_session_count(db: AsyncSession, user_id: int | None = None) -> int:
    from sqlalchemy import func
    stmt = select(func.count(models.Session.id))
    if user_id is not None:
        stmt = stmt.where(models.Session.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar() or 0

async def get_session_by_id(db: AsyncSession, session_id: int, user_id: int | None = None):
    stmt = select(models.Session).where(models.Session.id == session_id)
    if user_id is not None:
        stmt = stmt.where(models.Session.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_metrics_for_session(db: AsyncSession, session_id: int | None = None, user_id: int | None = None):
    stmt = select(models.PostureMetric)
    if session_id is not None:
        stmt = stmt.where(models.PostureMetric.session_id == session_id)
    if user_id is not None:
        stmt = stmt.where(models.PostureMetric.user_id == user_id)
    stmt = stmt.order_by(models.PostureMetric.timestamp.asc(), models.PostureMetric.id.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_alerts_for_session(db: AsyncSession, session_id: int | None = None, user_id: int | None = None):
    stmt = select(models.Alert)
    if session_id is not None:
        stmt = stmt.where(models.Alert.session_id == session_id)
    if user_id is not None:
        stmt = stmt.where(models.Alert.user_id == user_id)
    stmt = stmt.order_by(models.Alert.timestamp.asc(), models.Alert.id.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


