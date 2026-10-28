import os
import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import declarative_base

from ml.persistence import models, repositories, service

# Only run when DATABASE_URL points to MySQL
if not os.getenv("DATABASE_URL", "").startswith("mysql+aiomysql://"):
    pytest.skip("MySQL integration test skipped – DATABASE_URL not MySQL", allow_module_level=True)

engine = create_async_engine(os.getenv("DATABASE_URL"), future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def _setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    await _setup_db()
    async with AsyncSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_mysql_persistence_flow(db_session: AsyncSession):
    sess = await repositories.create_session(db_session, start_ts=1234.5)
    assert sess.id is not None
    metric = models.PostureMetric(
        session_id=sess.id,
        timestamp=1235.0,
        posture="TUP",
        confidence=0.95,
        risk_score=0.1,
        risk_level="NORMAL",
        temporal_state="NORMAL",
    )
    await repositories.add_metric(db_session, metric)
    metric2 = models.PostureMetric(
        session_id=sess.id,
        timestamp=1236.0,
        posture="TLF",
        confidence=0.88,
        risk_score=0.2,
        risk_level="WATCH",
        temporal_state="WATCH",
    )
    await repositories.add_metric(db_session, metric2)
    alert = models.Alert(
        session_id=sess.id,
        timestamp=1237.0,
        posture="TLF",
        risk_score=0.9,
        risk_level="ALERT",
        alert_type="RISK_ALERT",
        message="High risk detected",
    )
    await repositories.add_alert(db_session, alert)
    await repositories.finish_session(db_session, sess.id, end_ts=1240.0)
    # Verify counts
    result = await db_session.execute(
        text("SELECT COUNT(*) FROM posture_metrics WHERE session_id = :sid"), {"sid": sess.id}
    )
    assert result.scalar_one() == 2
    result2 = await db_session.execute(
        text("SELECT COUNT(*) FROM alerts WHERE session_id = :sid"), {"sid": sess.id}
    )
    assert result2.scalar_one() == 1
