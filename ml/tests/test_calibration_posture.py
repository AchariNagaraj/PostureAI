"""Tests for calibration-based posture evaluation and risk engine integration.

Covers:
1. Calibration does not create alert
2. Calibration does not increase persistence duration
3. Risk state resets after calibration
4. Upright after calibration = GOOD
5. Upright head = GOOD
6. Head tilt after calibration = BAD
7. Head tilt persistence creates alert
8. Returning head to neutral recovers
9. Genuine bad posture immediately after calibration still alerts
10. Invalid calibration sample ignored
11. Insufficient calibration samples fails
12. CalibrationBaseline median computation
13. evaluate_posture_rules with calibration vs without
14. InferenceEngine calibration state machine
"""
import time
import numpy as np
import pytest

from ml.inference.feature_extractor import (
    CalibrationBaseline,
    evaluate_posture_rules,
    head_pitch,
    head_roll,
    MIN_CALIBRATION_SAMPLES,
)
from ml.risk.temporal_risk_engine import TemporalRiskEngine, RiskState
from ml.risk.risk_config import TemporalRiskConfig


# ---------------------------------------------------------------------------
# Helpers — generate fake landmarks
# ---------------------------------------------------------------------------

class FakeLandmark:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


def _make_upright_landmarks():
    """Generate a 33-landmark set for a naturally upright person."""
    lms = [FakeLandmark(0.5, 0.5, 0.0)] * 33  # default fill

    # 0: nose
    lms[0] = FakeLandmark(0.50, 0.30, -0.03)
    # 7: left ear, 8: right ear
    lms[7] = FakeLandmark(0.40, 0.28, -0.04)
    lms[8] = FakeLandmark(0.60, 0.28, -0.04)
    # 11: left shoulder, 12: right shoulder
    lms[11] = FakeLandmark(0.35, 0.50, 0.00)
    lms[12] = FakeLandmark(0.65, 0.50, 0.00)
    # 13: left elbow, 14: right elbow
    lms[13] = FakeLandmark(0.30, 0.65, 0.0)
    lms[14] = FakeLandmark(0.70, 0.65, 0.0)
    # 23: left hip, 24: right hip
    lms[23] = FakeLandmark(0.40, 0.75, 0.00)
    lms[24] = FakeLandmark(0.60, 0.75, 0.00)
    return lms


def _make_head_tilted_landmarks():
    """Generate landmarks with clear head tilt to the left."""
    lms = _make_upright_landmarks()
    # Tilt head: left ear drops significantly, right ear rises
    lms[7] = FakeLandmark(0.38, 0.35, -0.04)   # left ear much lower
    lms[8] = FakeLandmark(0.62, 0.22, -0.04)    # right ear much higher
    # Also shift nose
    lms[0] = FakeLandmark(0.48, 0.32, -0.03)
    return lms


def _make_forward_lean_landmarks():
    """Generate landmarks with forward trunk lean."""
    lms = _make_upright_landmarks()
    # Lean forward: shift shoulders forward in z and adjust torso
    lms[11] = FakeLandmark(0.35, 0.48, -0.15)
    lms[12] = FakeLandmark(0.65, 0.48, -0.15)
    lms[0] = FakeLandmark(0.50, 0.25, -0.20)
    return lms


def _make_right_lean_landmarks():
    """Generate landmarks with right lateral trunk lean."""
    lms = _make_upright_landmarks()
    # Shift shoulders to the right relative to hips
    lms[11] = FakeLandmark(0.45, 0.50, 0.0)
    lms[12] = FakeLandmark(0.75, 0.50, 0.0)
    return lms


# ---------------------------------------------------------------------------
# CalibrationBaseline Tests
# ---------------------------------------------------------------------------

class TestCalibrationBaseline:
    def test_add_valid_sample(self):
        cb = CalibrationBaseline()
        lms = _make_upright_landmarks()
        assert cb.add_sample(lms, pose_valid=True)
        assert cb.sample_count == 1

    def test_reject_invalid_pose(self):
        cb = CalibrationBaseline()
        lms = _make_upright_landmarks()
        assert not cb.add_sample(lms, pose_valid=False)
        assert cb.sample_count == 0

    def test_reject_insufficient_landmarks(self):
        cb = CalibrationBaseline()
        short_lms = [FakeLandmark(0.5, 0.5)] * 10  # too few
        assert not cb.add_sample(short_lms, pose_valid=True)
        assert cb.sample_count == 0

    def test_finalize_requires_minimum_samples(self):
        cb = CalibrationBaseline()
        lms = _make_upright_landmarks()
        for _ in range(MIN_CALIBRATION_SAMPLES - 1):
            cb.add_sample(lms, pose_valid=True)
        assert not cb.finalize()
        assert not cb.is_calibrated

    def test_finalize_succeeds_with_enough_samples(self):
        cb = CalibrationBaseline()
        lms = _make_upright_landmarks()
        for _ in range(MIN_CALIBRATION_SAMPLES + 2):
            cb.add_sample(lms, pose_valid=True)
        assert cb.finalize()
        assert cb.is_calibrated
        assert cb.baseline is not None

    def test_baseline_uses_median(self):
        cb = CalibrationBaseline()
        lms = _make_upright_landmarks()
        # Add 7 identical samples
        for _ in range(7):
            cb.add_sample(lms, pose_valid=True)
        cb.finalize()

        expected_hp = head_pitch(lms)
        expected_hr = head_roll(lms)
        assert abs(cb.baseline['head_pitch'] - expected_hp) < 0.01
        assert abs(cb.baseline['head_roll'] - expected_hr) < 0.01

    def test_reset_clears_state(self):
        cb = CalibrationBaseline()
        lms = _make_upright_landmarks()
        for _ in range(7):
            cb.add_sample(lms, pose_valid=True)
        cb.finalize()
        assert cb.is_calibrated
        cb.reset()
        assert not cb.is_calibrated
        assert cb.sample_count == 0
        assert cb.baseline is None


# ---------------------------------------------------------------------------
# evaluate_posture_rules — calibrated vs uncalibrated
# ---------------------------------------------------------------------------

class TestPostureRulesWithCalibration:
    def _calibrated_baseline(self, lms):
        cb = CalibrationBaseline()
        for _ in range(7):
            cb.add_sample(lms, pose_valid=True)
        cb.finalize()
        return cb

    def test_upright_after_calibration_is_GOOD(self):
        lms = _make_upright_landmarks()
        cb = self._calibrated_baseline(lms)
        result = evaluate_posture_rules(lms, calibration=cb)
        assert result['head']['status'] == 'GOOD'
        assert result['shoulder']['status'] == 'GOOD'
        assert result['trunk']['status'] == 'GOOD'
        assert result['overall_status'] == 'GOOD'

    def test_head_tilt_after_calibration_is_BAD(self):
        upright = _make_upright_landmarks()
        cb = self._calibrated_baseline(upright)
        tilted = _make_head_tilted_landmarks()
        result = evaluate_posture_rules(tilted, calibration=cb)
        assert result['head']['status'] in ('MODERATE', 'BAD')
        assert result['overall_status'] != 'GOOD'

    def test_no_calibration_uses_absolute_thresholds(self):
        lms = _make_upright_landmarks()
        result = evaluate_posture_rules(lms, calibration=None)
        # Upright with typical landmarks should be GOOD under absolute thresholds too
        assert result['head']['status'] == 'GOOD'
        assert result['overall_status'] == 'GOOD'

    def test_forward_lean_after_calibration(self):
        upright = _make_upright_landmarks()
        cb = self._calibrated_baseline(upright)
        leaned = _make_forward_lean_landmarks()
        result = evaluate_posture_rules(leaned, calibration=cb)
        # Trunk should detect the lean
        assert result['trunk']['status'] in ('MODERATE', 'BAD')

    def test_right_lean_after_calibration(self):
        upright = _make_upright_landmarks()
        cb = self._calibrated_baseline(upright)
        leaned = _make_right_lean_landmarks()
        result = evaluate_posture_rules(leaned, calibration=cb)
        assert result['trunk']['status'] in ('MODERATE', 'BAD')


# ---------------------------------------------------------------------------
# Temporal Risk Engine — calibration boundary
# ---------------------------------------------------------------------------

class TestCalibrationRiskReset:
    def test_risk_engine_does_not_accumulate_during_calibration(self):
        """Simulate what happens: during calibration, the risk engine is
        never called. Verify from-scratch state."""
        cfg = TemporalRiskConfig(persistence_duration=3.0)
        engine = TemporalRiskEngine(cfg)
        # Before any processing, state should be NORMAL
        assert engine.state == RiskState.NORMAL
        assert engine._risky_start_ts is None
        assert engine._alert_event is None

    def test_risk_state_resets_after_calibration(self):
        """Simulate the calibration boundary: engine processes some frames,
        then _reset_state is called (as in InferenceEngine.finalize_calibration)."""
        cfg = TemporalRiskConfig(persistence_duration=3.0)
        engine = TemporalRiskEngine(cfg)
        t = time.time()

        # Simulate some bad posture frames (as if they leaked during calibration)
        for i in range(5):
            engine.process(
                timestamp=t + i,
                label="TLF",
                probabilities={"TLF": 0.95, "TUP": 0.05},
                posture_evaluation={"overall_status": "BAD"},
            )

        # After several frames, engine may be in ACTIVE_RISK
        # Now simulate calibration reset
        engine._reset_state()

        assert engine.state == RiskState.NORMAL
        assert engine._risky_start_ts is None
        assert engine._stable_start_ts is None
        assert engine._cooldown_end_ts is None
        assert engine._in_cooldown is False
        assert engine._alert_event is None

    def test_upright_after_reset_stays_NORMAL(self):
        cfg = TemporalRiskConfig(persistence_duration=3.0)
        engine = TemporalRiskEngine(cfg)
        engine._reset_state()
        t = time.time()

        # Process upright frames after reset
        for i in range(10):
            event = engine.process(
                timestamp=t + i,
                label="TUP",
                probabilities={"TUP": 0.95},
                confidence=0.95,
                posture_evaluation={"overall_status": "GOOD"},
            )
            assert event is None, f"Unexpected alert at frame {i}"
        assert engine.state == RiskState.NORMAL

    def test_genuine_bad_posture_after_reset_creates_alert(self):
        cfg = TemporalRiskConfig(persistence_duration=3.0, cooldown_duration=30.0)
        engine = TemporalRiskEngine(cfg)
        engine._reset_state()
        t = time.time()

        # Process BAD posture for longer than persistence_duration
        alert_seen = False
        for i in range(20):
            event = engine.process(
                timestamp=t + i,
                label="TLF",
                probabilities={"TLF": 0.95, "TUP": 0.05},
                confidence=0.95,
                posture_evaluation={"overall_status": "BAD"},
            )
            if event is not None:
                alert_seen = True
                break

        assert alert_seen, "Expected an alert for sustained bad posture after calibration"

    def test_calibration_does_not_create_alert_event(self):
        """During calibration (risk engine not called), no alert should exist."""
        cfg = TemporalRiskConfig(persistence_duration=3.0)
        engine = TemporalRiskEngine(cfg)
        # No process calls during calibration
        # After finalization, reset
        engine._reset_state()
        assert engine._alert_event is None

    def test_head_tilt_persistence_creates_alert(self):
        cfg = TemporalRiskConfig(persistence_duration=5.0, cooldown_duration=30.0)
        engine = TemporalRiskEngine(cfg)
        engine._reset_state()
        t = time.time()

        alert_seen = False
        for i in range(30):
            event = engine.process(
                timestamp=t + i * 0.5,
                label="TLR",
                probabilities={"TLR": 0.85, "TUP": 0.15},
                confidence=0.85,
                posture_evaluation={"overall_status": "BAD",
                                    "head": {"status": "BAD"},
                                    "shoulder": {"status": "GOOD"},
                                    "trunk": {"status": "GOOD"}},
            )
            if event is not None:
                alert_seen = True
                break
        assert alert_seen

    def test_returning_to_neutral_recovers(self):
        cfg = TemporalRiskConfig(
            persistence_duration=3.0,
            recovery_duration=3.0,
            cooldown_duration=5.0,
        )
        engine = TemporalRiskEngine(cfg)
        engine._reset_state()
        t = time.time()

        # First: sustained bad posture
        for i in range(10):
            engine.process(
                timestamp=t + i,
                label="TLF",
                probabilities={"TLF": 0.95, "TUP": 0.05},
                confidence=0.95,
                posture_evaluation={"overall_status": "BAD"},
            )

        # Then: cooldown passes, return to good
        t2 = t + 30  # well past cooldown
        for i in range(10):
            engine.process(
                timestamp=t2 + i,
                label="TUP",
                probabilities={"TUP": 0.95},
                confidence=0.95,
                posture_evaluation={"overall_status": "GOOD"},
            )
        # Should recover to NORMAL eventually
        assert engine.state == RiskState.NORMAL


# ---------------------------------------------------------------------------
# Integration — InferenceEngine calibration state machine
# ---------------------------------------------------------------------------

class TestInferenceEngineCalibration:
    @pytest.fixture(autouse=True)
    def _skip_if_no_model(self):
        """Skip these tests if the model file is not available."""
        from pathlib import Path
        candidates = [
            Path("ml/models/selected_development_model.joblib"),
            Path("ml/models/posture_model.joblib"),
            Path("models/viewpoint_robust_model.joblib"),
        ]
        if not any(c.is_file() for c in candidates):
            pytest.skip("Model file not available")

    def test_calibration_state_machine(self):
        from ml.inference.inference_service import InferenceEngine
        eng = InferenceEngine()
        assert eng.calibration_state == "IDLE"

        eng.start_calibration()
        assert eng.calibration_state == "CALIBRATING"

        lms = _make_upright_landmarks()
        for _ in range(10):
            result = eng.process(
                timestamp=time.time(),
                landmarks=lms,
                pose_valid=True,
            )
            # During calibration: no alert, zero risk
            assert result["alert_event"] is None
            assert result["risk_score"] == 0.0
            assert result["risk_level"] == "NORMAL"
            assert result["calibration_state"] == "CALIBRATING"

        success = eng.finalize_calibration()
        assert success
        assert eng.calibration_state == "CALIBRATION_COMPLETE"

    def test_upright_after_calibration_produces_GOOD(self):
        from ml.inference.inference_service import InferenceEngine
        eng = InferenceEngine()
        eng.start_calibration()
        lms = _make_upright_landmarks()
        for _ in range(10):
            eng.process(timestamp=time.time(), landmarks=lms, pose_valid=True)
        eng.finalize_calibration()

        # Now process upright frames in monitoring mode
        t = time.time()
        for i in range(10):
            result = eng.process(
                timestamp=t + i,
                landmarks=lms,
                pose_valid=True,
            )
            pe = result.get("posture_evaluation", {})
            assert pe.get("overall_status") == "GOOD", f"Expected GOOD at frame {i}, got {pe}"
            assert result["alert_event"] is None

    def test_head_tilt_after_calibration_detected(self):
        from ml.inference.inference_service import InferenceEngine
        eng = InferenceEngine()
        eng.start_calibration()
        lms = _make_upright_landmarks()
        for _ in range(10):
            eng.process(timestamp=time.time(), landmarks=lms, pose_valid=True)
        eng.finalize_calibration()

        tilted = _make_head_tilted_landmarks()
        result = eng.process(
            timestamp=time.time(),
            landmarks=tilted,
            pose_valid=True,
        )
        pe = result.get("posture_evaluation", {})
        assert pe.get("head", {}).get("status") in ("MODERATE", "BAD")
