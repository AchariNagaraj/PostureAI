import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select
from ml.persistence import models, repositories, service

@pytest_asyncio.fixture(scope="function")
async def db_session():
    # Use an in‑memory SQLite DB for isolation.
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with test_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async_session = service.db.AsyncSessionLocal
    # Override the sessionmaker to use our test engine
    async_session = service.db.async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await test_engine.dispose()

@pytest.mark.asyncio
async def test_session_lifecycle(db_session: AsyncSession):
    sess = await repositories.create_session(db_session, start_ts=1234.5)
    assert sess.id is not None
    assert sess.start_timestamp == 1234.5
    finished = await repositories.finish_session(db_session, sess.id, end_ts=5678.9)
    assert finished.status == "COMPLETED"
    assert finished.end_timestamp == 5678.9

@pytest.mark.asyncio
async def test_metric_and_alert_persistence(db_session: AsyncSession):
    sess = await repositories.create_session(db_session, start_ts=1000.0)
    metric = models.PostureMetric(
        session_id=sess.id,
        timestamp=1001.0,
        posture="TUP",
        confidence=0.9,
        risk_score=0.1,
        risk_level="NORMAL",
        temporal_state="NORMAL",
        viewpoint=None,
        tracking_state=None,
        pose_valid=True,
    )
    await repositories.add_metric(db_session, metric)
    result = await db_session.execute(select(models.PostureMetric).where(models.PostureMetric.session_id == sess.id))
    fetched = result.scalars().first()
    assert fetched is not None
    assert fetched.posture == "TUP"

    alert = models.Alert(
        session_id=sess.id,
        timestamp=1002.0,
        posture="TLF",
        risk_score=0.8,
        risk_level="ALERT",
        alert_type="RISK_ALERT",
        message="Risk sustained",
        voice_message=None,
        viewpoint=None,
        risk_state="ACTIVE_RISK",
    )
    await repositories.add_alert(db_session, alert)
    result2 = await db_session.execute(select(models.Alert).where(models.Alert.session_id == sess.id))
    fetched_alert = result2.scalars().first()
    assert fetched_alert is not None
    assert fetched_alert.risk_level == "ALERT"

@pytest.mark.asyncio
async def test_service_persist_event(db_session: AsyncSession, monkeypatch):
    # Monkey‑patch the sessionmaker to return our test session.
    monkeypatch.setattr(service.db, "AsyncSessionLocal", lambda: db_session)
    payload = {
        "timestamp": 2000.0,
        "posture": "TUP",
        "confidence": 0.95,
        "risk_score": 0.05,
        "risk_level": "NORMAL",
        "temporal_state": "NORMAL",
        "viewpoint": None,
        "tracking_state": None,
        "pose_valid": True,
    }
    await service.persist_event("POSTURE_UPDATE", payload)
    result = await db_session.execute(select(models.PostureMetric))
    metric = result.scalars().first()
    assert metric is not None
    assert metric.posture == "TUP"

    alert_payload = {
        "timestamp": 2001.0,
        "posture": "TLF",
        "risk_score": 0.9,
        "risk_level": "ALERT",
        "temporal_state": "ACTIVE_RISK",
        "alert_type": "RISK_ALERT",
        "message": "High risk",
    }
    await service.persist_event("ALERT", alert_payload)
    result2 = await db_session.execute(select(models.Alert))
    alert = result2.scalars().first()
    assert alert is not None
    assert alert.message == "High risk"
