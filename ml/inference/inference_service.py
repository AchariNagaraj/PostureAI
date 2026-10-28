import time
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

from .feature_extractor import FEATURE_FUNCS, CalibrationBaseline, evaluate_posture_rules
from ..risk.temporal_risk_engine import TemporalRiskEngine
from ..risk.risk_config import TemporalRiskConfig

# Load the viewpoint-robust model (Phase 2 artifact)
MODEL_CANDIDATES = [
    Path("ml/models/selected_development_model.joblib"),
    Path("ml/models/posture_model.joblib"),
    Path("models/viewpoint_robust_model.joblib"),
]

MODEL_PATH = None
for candidate in MODEL_CANDIDATES:
    if candidate.is_file():
        MODEL_PATH = candidate
        break

if not MODEL_PATH:
    raise FileNotFoundError("Model file not found in candidates: " + ", ".join(str(p) for p in MODEL_CANDIDATES))

_MODEL = joblib.load(MODEL_PATH)

class InferenceEngine:
    """Core service that runs a single inference cycle.

    It accepts raw MediaPipe landmarks (or a pre‑computed label/probabilities) and
    returns a rich, structured dictionary that will be streamed to the frontend.
    """

    # Calibration states
    CALIB_IDLE = "IDLE"
    CALIB_CALIBRATING = "CALIBRATING"
    CALIB_COMPLETE = "CALIBRATION_COMPLETE"

    def __init__(self, config: Optional[TemporalRiskConfig] = None):
        self.cfg = config or TemporalRiskConfig()
        self.risk_engine = TemporalRiskEngine(self.cfg)
        self.model = _MODEL
        self.calibration = CalibrationBaseline()
        self._calibration_state = self.CALIB_IDLE

    @property
    def calibration_state(self) -> str:
        return self._calibration_state

    def start_calibration(self):
        """Enter calibration mode — resets calibration baseline and risk state."""
        self.calibration.reset()
        self._calibration_state = self.CALIB_CALIBRATING
        # Pre-emptively reset risk so no stale state leaks
        self.risk_engine._reset_state()

    def finalize_calibration(self) -> bool:
        """Finalize calibration — compute baseline, reset risk, transition to COMPLETE.
        Returns True if calibration succeeded (enough valid samples)."""
        success = self.calibration.finalize()
        if success:
            self._calibration_state = self.CALIB_COMPLETE
            # CRITICAL: full reset of temporal risk state at calibration boundary
            self.risk_engine._reset_state()
        return success

    def _extract_features(self, landmarks: List[Any]) -> List[float]:
        """Extract the eight engineered features from MediaPipe landmarks.
        The function mirrors the logic in ``scripts/webcam_inference.py``.
        """
        return [fn(landmarks) for fn in FEATURE_FUNCS]

    def _predict(self, features: List[float]) -> Dict[str, float]:
        """Run the RandomForest model and return a probability dict.
        ``model.predict`` returns the class label; ``model.predict_proba`` gives the
        per‑class probabilities in the order of ``model.classes_``.
        """
        probs = self.model.predict_proba(np.array(features).reshape(1, -1))[0]
        prob_dict = dict(zip(self.model.classes_, probs))
        return prob_dict

    def process(
        self,
        *,
        timestamp: float,
        landmarks: Optional[List[Any]] = None,
        label: Optional[str] = None,
        probabilities: Optional[Dict[str, float]] = None,
        confidence: Optional[float] = None,
        viewpoint: Optional[str] = None,
        tracking_state: Optional[str] = None,
        pose_valid: Optional[bool] = None,
        invalid_state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a full inference step.

        The method follows the existing pipeline – feature extraction → model
        prediction → confidence calculation → temporal risk engine → structured
        output.

        During calibration (CALIBRATING state), samples are collected but the
        risk engine is NOT invoked and no alerts are generated.
        """
        is_calibrating = self._calibration_state == self.CALIB_CALIBRATING

        # -----------------------------------------------------------------
        # 1️⃣  Feature extraction / model prediction (if not supplied)
        # -----------------------------------------------------------------
        if probabilities is None:
            if landmarks is None:
                raise ValueError("Either `probabilities` or `landmarks` must be provided")
            features = self._extract_features(landmarks)
            probabilities = self._predict(features)
        if label is None:
            # deterministic pick of highest probability
            label = max(probabilities, key=probabilities.get)
        if confidence is None:
            confidence = max(probabilities.values())

        # -----------------------------------------------------------------
        # CALIBRATION: collect sample, skip risk engine
        # -----------------------------------------------------------------
        if is_calibrating:
            if landmarks is not None and pose_valid is not False:
                self.calibration.add_sample(landmarks, pose_valid=True)

            # Evaluate posture rules WITHOUT calibration baseline (informational only)
            posture_eval = evaluate_posture_rules(landmarks, calibration=None)

            # Build a safe output with NO risk, NO alerts
            output = {
                "timestamp": timestamp,
                "posture": label,
                "class_probabilities": probabilities,
                "confidence": confidence,
                "viewpoint": viewpoint,
                "tracking_state": tracking_state,
                "pose_valid": pose_valid,
                "risk_score": 0.0,
                "risk_level": "NORMAL",
                "temporal_state": "NORMAL",
                "alert_event": None,
                "recommendation": None,
                "posture_evaluation": posture_eval,
                "calibration_state": self._calibration_state,
                "calibration_info": self.calibration.get_debug_info(),
            }
            return output

        # -----------------------------------------------------------------
        # 2️⃣  Deterministic rule-based posture evaluation (with calibration)
        # -----------------------------------------------------------------
        calib = self.calibration if self.calibration.is_calibrated else None
        posture_eval = evaluate_posture_rules(landmarks, calibration=calib)

        # -----------------------------------------------------------------
        # 3️⃣  Temporal risk engine handling
        # -----------------------------------------------------------------
        alert_event = self.risk_engine.process(
            timestamp=timestamp,
            label=label,
            probabilities=probabilities,
            confidence=confidence,
            viewpoint=viewpoint,
            tracking_state=tracking_state,
            pose_valid=pose_valid,
            invalid_state=invalid_state,
            posture_evaluation=posture_eval,
        )

        # -----------------------------------------------------------------
        # 4️⃣  Assemble the structured monitoring payload
        # -----------------------------------------------------------------
        recommendation = None
        eval_status = posture_eval.get("overall_status")
        if alert_event or eval_status == "BAD" or (label != "TUP" and eval_status != "GOOD"):
            recommendation = {
                "title": "Postural Alignment Guidance",
                "description": "You're compromising with your posture. Please correct your posture.",
            }

        output = {
            "timestamp": timestamp,
            "posture": label,
            "class_probabilities": probabilities,
            "confidence": confidence,
            "viewpoint": viewpoint,
            "tracking_state": tracking_state,
            "pose_valid": pose_valid,
            "risk_score": (0.95 if posture_eval.get("overall_status") == "BAD" else (0.45 if posture_eval.get("overall_status") == "MODERATE" else self.risk_engine.cfg.risk_mapping.get(label, 0.0) * confidence)),
            "risk_level": ("ALERT" if alert_event else "NORMAL"),
            "temporal_state": self.risk_engine.state.value,
            "alert_event": alert_event,
            "recommendation": recommendation,
            "posture_evaluation": posture_eval,
            "calibration_state": self._calibration_state,
        }
        return output
