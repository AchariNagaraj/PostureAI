# ml/tests/test_analytics.py
"""Comprehensive pytest suite for Phase 9 Analytics Service and Router endpoints."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ml.persistence import models, repositories
from ml.analytics import service as analytics_service


@pytest_asyncio.fixture(scope="function")
async def test_db_session():
    """Create an isolated in-memory SQLite database session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_empty_database_analytics(test_db_session: AsyncSession):
    """Verify zeroed JSON structure when database has no records."""
    summary = await analytics_service.get_summary_analytics(test_db_session)
    assert summary["total_sessions"] == 0
    assert summary["completed_sessions"] == 0
    assert summary["total_observed_duration_seconds"] == 0.0
    assert summary["total_alerts"] == 0
    assert summary["upright_duration_ratio"] == 0.0
    assert summary["highest_observed_risky_posture_by_duration"] is None

    postures = await analytics_service.get_posture_analytics(test_db_session)
    assert postures["total_observation_count"] == 0
    assert postures["total_observed_duration_seconds"] == 0.0
    assert postures["upright_duration_ratio"] == 0.0
    assert postures["transitions"] == {}


@pytest.mark.asyncio
async def test_timestamp_duration_calculation(test_db_session: AsyncSession):
    """Verify interval math and final metric duration = 0 rule."""
    sess = await repositories.create_session(test_db_session, start_ts=1000.0)

    # 3 metrics: t=1000 (TUP), t=1002 (TLF), t=1005 (TUP)
    m1 = models.PostureMetric(session_id=sess.id, timestamp=1000.0, posture="TUP", confidence=0.9, risk_score=0.0, risk_level="NORMAL", temporal_state="NORMAL")
    m2 = models.PostureMetric(session_id=sess.id, timestamp=1002.0, posture="TLF", confidence=0.9, risk_score=1.0, risk_level="WATCH", temporal_state="WATCH")
    m3 = models.PostureMetric(session_id=sess.id, timestamp=1005.0, posture="TUP", confidence=0.9, risk_score=0.0, risk_level="NORMAL", temporal_state="NORMAL")

    await repositories.add_metric(test_db_session, m1)
    await repositories.add_metric(test_db_session, m2)
    await repositories.add_metric(test_db_session, m3)

    stats = await analytics_service.get_posture_analytics(test_db_session, session_id=sess.id)

    # total duration: (1002-1000) + (1005-1002) + 0 (final m3) = 2.0 + 3.0 = 5.0s
    assert stats["total_observed_duration_seconds"] == 5.0
    assert stats["postures"]["TUP"]["duration_seconds"] == 2.0
    assert stats["postures"]["TLF"]["duration_seconds"] == 3.0


@pytest.mark.asyncio
async def test_final_metric_duration_is_zero(test_db_session: AsyncSession):
    """Verify final metric in sequence is assigned strictly 0.0s duration."""
    sess = await repositories.create_session(test_db_session, start_ts=500.0)

    m1 = models.PostureMetric(session_id=sess.id, timestamp=500.0, posture="TLF", confidence=0.9, risk_score=1.0, risk_level="WATCH", temporal_state="WATCH")
    m2 = models.PostureMetric(session_id=sess.id, timestamp=504.0, posture="TLF", confidence=0.9, risk_score=1.0, risk_level="WATCH", temporal_state="WATCH")

    await repositories.add_metric(test_db_session, m1)
    await repositories.add_metric(test_db_session, m2)

    stats = await analytics_service.get_posture_analytics(test_db_session, session_id=sess.id)

    # m1 gets 4.0s duration. m2 gets 0.0s. Total = 4.0s.
    assert stats["total_observed_duration_seconds"] == 4.0
    assert stats["postures"]["TLF"]["duration_seconds"] == 4.0


@pytest.mark.asyncio
async def test_posture_transitions_count_within_gmax(test_db_session: AsyncSession):
    """Verify posture transitions <= G_MAX (10.0s) are counted."""
    sess = await repositories.create_session(test_db_session, start_ts=100.0)

    m1 = models.PostureMetric(session_id=sess.id, timestamp=100.0, posture="TUP", confidence=0.9, risk_score=0.0, risk_level="NORMAL", temporal_state="NORMAL")
    m2 = models.PostureMetric(session_id=sess.id, timestamp=105.0, posture="TLF", confidence=0.9, risk_score=1.0, risk_level="WATCH", temporal_state="WATCH") # delta_t = 5.0s <= 10s

    await repositories.add_metric(test_db_session, m1)
    await repositories.add_metric(test_db_session, m2)

    stats = await analytics_service.get_posture_analytics(test_db_session, session_id=sess.id)
    assert stats["transitions"] == {"TUP->TLF": 1}


@pytest.mark.asyncio
async def test_posture_transitions_ignored_across_gap(test_db_session: AsyncSession):
    """Verify posture changes across an unobserved gap (> 10.0s) generate ZERO transition count."""
    sess = await repositories.create_session(test_db_session, start_ts=100.0)

    m1 = models.PostureMetric(session_id=sess.id, timestamp=100.0, posture="TLF", confidence=0.9, risk_score=1.0, risk_level="WATCH", temporal_state="WATCH")
    m2 = models.PostureMetric(session_id=sess.id, timestamp=125.0, posture="TUP", confidence=0.9, risk_score=0.0, risk_level="NORMAL", temporal_state="NORMAL") # delta_t = 25s > G_MAX

    await repositories.add_metric(test_db_session, m1)
    await repositories.add_metric(test_db_session, m2)

    stats = await analytics_service.get_posture_analytics(test_db_session, session_id=sess.id)

    # Gap > 10s -> NO transition credited, NO duration credited
    assert stats["transitions"] == {}
    assert stats["total_observed_duration_seconds"] == 0.0


@pytest.mark.asyncio
async def test_duplicate_timestamps_transition_ordering(test_db_session: AsyncSession):
    """Verify deterministic (timestamp ASC, id ASC) ordering for duplicate timestamps."""
    sess = await repositories.create_session(test_db_session, start_ts=10.0)

    m1 = models.PostureMetric(session_id=sess.id, timestamp=10.0, posture="TUP", confidence=0.9, risk_score=0.0, risk_level="NORMAL", temporal_state="NORMAL")
    m2 = models.PostureMetric(session_id=sess.id, timestamp=10.0, posture="TLF", confidence=0.9, risk_score=1.0, risk_level="WATCH", temporal_state="WATCH")
    m3 = models.PostureMetric(session_id=sess.id, timestamp=14.0, posture="TLF", confidence=0.9, risk_score=1.0, risk_level="WATCH", temporal_state="WATCH")

    await repositories.add_metric(test_db_session, m1)
    await repositories.add_metric(test_db_session, m2)
    await repositories.add_metric(test_db_session, m3)

    stats = await analytics_service.get_posture_analytics(test_db_session, session_id=sess.id)

    # m1->m2: delta_t = 0.0s <= 10.0s, posture TUP->TLF -> counted transition
    # m2->m3: delta_t = 4.0s <= 10.0s, posture TLF->TLF -> no transition
    assert stats["transitions"] == {"TUP->TLF": 1}
    assert stats["total_observed_duration_seconds"] == 4.0


@pytest.mark.asyncio
async def test_single_metric_session(test_db_session: AsyncSession):
    """Verify single metric session yields 0.0s duration and duration_reliable = false."""
    sess = await repositories.create_session(test_db_session, start_ts=10.0)

    m1 = models.PostureMetric(session_id=sess.id, timestamp=10.0, posture="TUP", confidence=0.9, risk_score=0.0, risk_level="NORMAL", temporal_state="NORMAL")
    await repositories.add_metric(test_db_session, m1)

    metrics = await repositories.get_metrics_for_session(test_db_session, session_id=sess.id)
    stats = analytics_service.process_metric_intervals(metrics)

    assert stats["total_observations"] == 1
    assert stats["total_observed_duration_seconds"] == 0.0
    assert stats["duration_reliable"] is False


@pytest.mark.asyncio
async def test_utc_midnight_splitting(test_db_session: AsyncSession):
    """Verify metric interval crossing UTC midnight is split correctly across UTC dates."""
    sess = await repositories.create_session(test_db_session, start_ts=1759017595.0)

    # t1: 2025-09-27 23:59:55 UTC (timestamp = 1759017595)
    # t2: 2025-09-28 00:00:05 UTC (timestamp = 1759017605) -> delta_t = 10.0s <= 10s
    t1 = datetime(2025, 9, 27, 23, 59, 55, tzinfo=timezone.utc).timestamp()
    t2 = datetime(2025, 9, 28, 0, 0, 5, tzinfo=timezone.utc).timestamp()

    m1 = models.PostureMetric(session_id=sess.id, timestamp=t1, posture="TUP", confidence=0.9, risk_score=0.0, risk_level="NORMAL", temporal_state="NORMAL")
    m2 = models.PostureMetric(session_id=sess.id, timestamp=t2, posture="TUP", confidence=0.9, risk_score=0.0, risk_level="NORMAL", temporal_state="NORMAL")

    await repositories.add_metric(test_db_session, m1)
    await repositories.add_metric(test_db_session, m2)

    metrics = await repositories.get_metrics_for_session(test_db_session, session_id=sess.id)
    stats = analytics_service.process_metric_intervals(metrics)

    # 5 seconds credited to 2025-09-27, 5 seconds credited to 2025-09-28
    daily = stats["daily_durations_utc"]
    assert daily["2025-09-27"] == 5.0
    assert daily["2025-09-28"] == 5.0


@pytest.mark.asyncio
async def test_timeline_downsampling_preserves_alerts_and_transitions(test_db_session: AsyncSession):
    """Verify timeline downsampling explicitly preserves alerts and transition points."""
    sess = await repositories.create_session(test_db_session, start_ts=0.0)

    # Create 50 metrics with a posture transition at index 20 and an alert at index 35
    metrics = []
    for i in range(50):
        p = "TUP" if i < 20 else "TLF"
        m = models.PostureMetric(session_id=sess.id, timestamp=float(i), posture=p, confidence=0.9, risk_score=0.0, risk_level="NORMAL", temporal_state="NORMAL")
        metrics.append(m)

    alert = models.Alert(session_id=sess.id, timestamp=35.0, posture="TLF", risk_score=1.0, risk_level="ALERT", alert_type="PERSISTENT_TLF")
    alerts = [alert]

    # Downsample to maximum 10 points
    downsampled = analytics_service.downsample_timeline(metrics, alerts, max_points=10)

    timestamps = [item["timestamp"] for item in downsampled]

    # Verify first (0.0), last (49.0), transition boundaries (19.0, 20.0), and alert (35.0) are preserved
    assert 0.0 in timestamps
    assert 49.0 in timestamps
    assert 19.0 in timestamps or 20.0 in timestamps
    assert 35.0 in timestamps
    assert any(item["is_alert_event"] for item in downsampled if item["timestamp"] == 35.0)
