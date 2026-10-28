# ml/tests/test_phase10_full_integration.py
"""Full system integration test suite for Phase 10 (Steps 1–9).

Verifies the end-to-end processing pipeline from frame decoding to ML inference,
TemporalRiskEngine state machine, WebSocket payload contract, database persistence,
and Phase 9 analytics aggregation.
"""

import pytest
import pytest_asyncio
import base64
import cv2
import numpy as np
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ml.persistence import models, repositories, service as persistence_service
from ml.inference.pose_processor import PoseProcessor
from ml.inference.target_tracker import TargetTracker
from ml.inference.viewpoint_estimator import estimate_viewpoint
from ml.inference.inference_service import InferenceEngine
from ml.risk.risk_config import TemporalRiskConfig
from ml.analytics import service as analytics_service


@pytest_asyncio.fixture(scope="function")
async def test_db_session():
    """Create isolated in-memory SQLite database session for integration tests."""
    persistence_service._current_session_id = None
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    persistence_service._current_session_id = None
    await engine.dispose()


class MockLandmark:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


def generate_mock_landmarks(dx=0.0, dy=0.0, dz=0.0):
    landmarks = [MockLandmark(0.5, 0.5, 0.0) for _ in range(33)]
    landmarks[11] = MockLandmark(0.4 + dx, 0.5 + dy, 0.0 + dz)
    landmarks[12] = MockLandmark(0.6 + dx, 0.5 + dy, 0.0)
    return landmarks


def generate_jpeg_base64(width=100, height=100) -> str:
    img = np.zeros((height, width, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", img)
    return base64.b64encode(buffer).decode("utf-8")


@pytest.mark.asyncio
async def test_end_to_end_frame_to_persistence_flow(test_db_session: AsyncSession):
    """Verify complete flow: Frame -> Pose -> Target -> Viewpoint -> ML -> Risk -> Persistence."""
    pose_processor = PoseProcessor()
    target_tracker = TargetTracker()
    inference_engine = InferenceEngine()

    # Create dummy base64 JPEG
    b64_frame = generate_jpeg_base64()
    pose_valid, raw_landmarks = pose_processor.process_base64_frame(b64_frame)

    # Blank frame returns pose_valid = False
    assert pose_valid is False or raw_landmarks is None

    # Use valid mock landmarks to test inference + risk + persistence flow
    mock_lm = generate_mock_landmarks()
    cand = {
        "temp_id": 1,
        "bbox": {"x": 0.1, "y": 0.1, "width": 0.5, "height": 0.8},
        "center": (0.35, 0.5),
        "landmarks": mock_lm,
        "confidence": 0.95,
    }
    target_info = target_tracker.process_candidates([cand])
    assert target_info["pose_valid"] is True
    assert target_info["tracking_state"] == "TARGET_TRACKING"

    vp = estimate_viewpoint(target_info["active_landmarks"])
    assert vp == "FRONT"

    t0 = 1000.0
    result = inference_engine.process(
        timestamp=t0,
        landmarks=target_info["active_landmarks"],
        viewpoint=vp,
        tracking_state=target_info["tracking_state"],
        pose_valid=True,
    )

    assert "posture" in result
    assert "class_probabilities" in result
    assert result["risk_level"] in ["NORMAL", "ALERT"]

    # Persist posture metric
    session_id = await persistence_service._get_or_create_session(test_db_session, t0)
    metric = models.PostureMetric(
        session_id=session_id,
        timestamp=t0,
        posture=result["posture"],
        confidence=result["confidence"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        temporal_state=result["temporal_state"],
        viewpoint=result["viewpoint"],
        tracking_state=result["tracking_state"],
        pose_valid=result["pose_valid"],
    )
    await repositories.add_metric(test_db_session, metric)

    # Close session
    await persistence_service.close_session(test_db_session, end_timestamp=t0 + 10.0)

    # Verify session persisted correctly
    sess = await repositories.get_session_by_id(test_db_session, session_id)
    assert sess is not None
    assert sess.status == "COMPLETED"
    assert sess.end_timestamp == t0 + 10.0

    pose_processor.close()
    target_tracker.reset()


@pytest.mark.asyncio
async def test_persistent_risk_alert_generation_and_analytics(test_db_session: AsyncSession):
    """Verify persistent risk triggers alert event, gets stored in DB, and appears in Phase 9 report."""
    config = TemporalRiskConfig(persistence_duration=10.0)
    inference_engine = InferenceEngine(config=config)
    sess = await repositories.create_session(test_db_session, start_ts=2000.0)

    # Simulate 15 seconds of persistent TLF (leaning forward) to trigger alert
    start_ts = 2000.0
    alert_triggered = False

    for i in range(16):
        ts = start_ts + i
        result = inference_engine.process(
            timestamp=ts,
            label="TLF",
            probabilities={"TLF": 0.95, "TUP": 0.05},
            viewpoint="FRONT",
            tracking_state="TRACKING",
            pose_valid=True,
        )

        # Store metric
        m = models.PostureMetric(
            session_id=sess.id,
            timestamp=ts,
            posture=result["posture"],
            confidence=result["confidence"],
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            temporal_state=result["temporal_state"],
            viewpoint=result["viewpoint"],
            tracking_state=result["tracking_state"],
            pose_valid=result["pose_valid"],
        )
        await repositories.add_metric(test_db_session, m)

        if result["alert_event"]:
            alert_triggered = True
            al = result["alert_event"]
            alert_obj = models.Alert(
                session_id=sess.id,
                timestamp=al["timestamp"],
                posture=al["posture"],
                risk_score=al["risk_score"],
                risk_level=al["risk_level"],
                alert_type=al["alert_type"],
                message=al["message"],
                voice_message=al["voice_message"],
            )
            await repositories.add_alert(test_db_session, alert_obj)

    assert alert_triggered is True

    # Complete session
    await repositories.finish_session(test_db_session, sess.id, end_ts=2020.0)

    # Query Phase 9 session report
    report = await analytics_service.get_session_report(test_db_session, sess.id)
    assert report is not None
    assert report["session_id"] == sess.id
    assert report["total_alerts"] >= 1
    assert report["primary_risky_posture_by_duration"] == "TLF"
    assert "TLF" in report["engineering_summary"]
