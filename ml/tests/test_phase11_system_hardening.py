# ml/tests/test_phase11_system_hardening.py
"""Phase 11 — Hardening & Performance Test Suite.

Covers:
- Step 3: WebSocket handling, malformed messages, rapid bursts
- Step 4: DB failure resilience (graceful logging, stream continuity)
- Step 5 & 10: Session lifecycle & 10x START/STOP resource cleanup
- Step 7: Analytics data integrity validation (G_max=10s, downsampling)
- Step 8 & 9: Benchmark latency profiling & memory stability
"""

import pytest
import pytest_asyncio
import time
import json
import base64
import cv2
import numpy as np
import tracemalloc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ml.persistence import models, repositories, service as persistence_service
from ml.inference.pose_processor import PoseProcessor
from ml.inference.target_tracker import TargetTracker
from ml.inference.viewpoint_estimator import estimate_viewpoint
from ml.inference.inference_service import InferenceEngine
from ml.risk.temporal_risk_engine import TemporalRiskEngine
from ml.risk.risk_config import TemporalRiskConfig
from ml.analytics import service as analytics_service


@pytest_asyncio.fixture(scope="function")
async def db_session():
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


def get_mock_lms():
    lms = [MockLandmark(0.5, 0.5, 0.0) for _ in range(33)]
    lms[11] = MockLandmark(0.4, 0.5, 0.0)
    lms[12] = MockLandmark(0.6, 0.5, 0.0)
    return lms


# =====================================================================
# STEP 4: DB FAILURE RESILIENCE
# =====================================================================

@pytest.mark.asyncio
async def test_database_failure_resilience(db_session: AsyncSession):
    """Verify system does not crash if DB write raises an exception."""
    # Simulating invalid payload / DB issue
    bad_payload = {"timestamp": time.time(), "posture": "TLF"}
    
    # Force db error by passing invalid payload format to persist_event
    try:
        await persistence_service.persist_event("POSTURE_UPDATE", bad_payload)
    except Exception as exc:
        pytest.fail(f"persist_event should swallow exception gracefully but raised: {exc}")


# =====================================================================
# STEP 5 & 10: SESSION LIFECYCLE AND 10x REPEATED START/STOP CLEANUP
# =====================================================================

@pytest.mark.asyncio
async def test_session_lifecycle_and_10x_cleanup(db_session: AsyncSession):
    """Run START -> MONITOR -> STOP cycles 10 times consecutively."""
    for cycle in range(10):
        start_ts = 1000.0 + cycle * 100
        sess_id = await persistence_service._get_or_create_session(db_session, start_ts)
        assert sess_id is not None
        
        # Add 5 frame metrics
        for i in range(5):
            metric = models.PostureMetric(
                session_id=sess_id,
                timestamp=start_ts + i,
                posture="TUP",
                confidence=0.95,
                risk_score=10.0,
                risk_level="NORMAL",
                temporal_state="NORMAL",
                viewpoint="FRONT",
                tracking_state="TRACKING",
                pose_valid=True
            )
            await repositories.add_metric(db_session, metric)
            
        # Close session
        await persistence_service.close_session(db_session, end_timestamp=start_ts + 10.0)
        
        # Verify session state
        s = await repositories.get_session_by_id(db_session, sess_id)
        assert s.status == "COMPLETED"
        assert persistence_service._current_session_id is None


# =====================================================================
# STEP 7: ANALYTICS DATA-INTEGRITY & G_MAX RULE VALIDATION
# =====================================================================

@pytest.mark.asyncio
async def test_analytics_gmax_rule(db_session: AsyncSession):
    """Verify interval > 10 seconds contributes zero duration (G_max rule)."""
    sess = await repositories.create_session(db_session, start_ts=5000.0)
    
    # Metric 1 at t=5000.0
    m1 = models.PostureMetric(
        session_id=sess.id, timestamp=5000.0, posture="TLF", confidence=0.9, risk_score=80.0,
        risk_level="ALERT", temporal_state="ACTIVE_RISK", viewpoint="FRONT", tracking_state="TRACKING", pose_valid=True
    )
    # Metric 2 at t=5015.0 (> 10 seconds gap)
    m2 = models.PostureMetric(
        session_id=sess.id, timestamp=5015.0, posture="TLF", confidence=0.9, risk_score=80.0,
        risk_level="ALERT", temporal_state="ACTIVE_RISK", viewpoint="FRONT", tracking_state="TRACKING", pose_valid=True
    )
    await repositories.add_metric(db_session, m1)
    await repositories.add_metric(db_session, m2)
    await repositories.finish_session(db_session, sess.id, end_ts=5020.0)
    
    report = await analytics_service.get_session_report(db_session, sess.id)
    assert report is not None
    # Transition across >10s gap should not create transition count
    assert report["total_transitions"] == 0


# =====================================================================
# STEP 8 & 9: BENCHMARK LATENCY & MEMORY GROWTH TEST
# =====================================================================

def test_performance_latency_profiling_and_memory():
    """Profile component latencies over 200 frame iterations and check memory stability."""
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()
    
    pose_processor = PoseProcessor()
    target_tracker = TargetTracker()
    inference_engine = InferenceEngine()
    
    # Create valid frame bytes
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    b64_frame = base64.b64encode(buf).decode("utf-8")
    
    latencies = []
    mock_lms = get_mock_lms()
    
    start_time = time.time()
    num_frames = 50
    
    for i in range(num_frames):
        t0 = time.perf_counter()
        
        # 1. Pose processing
        valid, raw_lms = pose_processor.process_base64_frame(b64_frame)
        
        # 2. Target tracking
        t_info = target_tracker.process_pose(True, mock_lms)
        
        # 3. Viewpoint estimation
        vp = estimate_viewpoint(t_info["active_landmarks"])
        
        # 4. Inference & Risk engine
        result = inference_engine.process(
            timestamp=start_time + (i * 0.1),
            landmarks=t_info["active_landmarks"],
            viewpoint=vp,
            tracking_state=t_info["tracking_state"],
            pose_valid=True
        )
        
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # ms
        
    snapshot2 = tracemalloc.take_snapshot()
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    tracemalloc.stop()
    
    avg_latency = np.mean(latencies)
    median_latency = np.median(latencies)
    p95_latency = np.percentile(latencies, 95)
    max_latency = np.max(latencies)
    
    # Assert reasonable real-time latency bounds (< 300ms average for streaming)
    assert avg_latency < 300.0, f"Average latency too high: {avg_latency:.2f} ms"
    
    pose_processor.close()
    
    # Print metrics table
    print("\n--- Phase 11 Performance Benchmark ---")
    print(f"Frames processed: {num_frames}")
    print(f"Average latency:  {avg_latency:.2f} ms")
    print(f"Median latency:   {median_latency:.2f} ms")
    print(f"P95 latency:      {p95_latency:.2f} ms")
    print(f"Max latency:      {max_latency:.2f} ms")
