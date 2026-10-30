"""Research‑grade temporal risk engine.

This module implements the full pipeline described in Phase 4:

1️⃣ Posture → risk mapping (configurable)
2️⃣ Confidence‑aware risk score
3️⃣ Deterministic temporal smoothing (label stability)
4️⃣ Persistence / recovery / cooldown state machine
5️⃣ Structured alert event generation (including optional voice message)

The design mirrors the architecture diagram in the master context and is deliberately
independent of any model‑training code.
"""

import enum
import time
from typing import Dict, Any, Optional, Tuple

from .risk_config import TemporalRiskConfig


class RiskState(enum.Enum):
    """State machine for temporal risk handling."""
    NORMAL = "NORMAL"
    ACTIVE_RISK = "ACTIVE_RISK"
    RECOVERING = "RECOVERING"
    COOLDOWN = "COOLDOWN"
    WATCH = "WATCH"


class TemporalRiskEngine:
    """Core engine that ingests per‑frame posture information and emits alerts.

    The engine is *research‑grade*: all thresholds, mappings and durations are
    configurable via :class:`TemporalRiskConfig`.  No assumptions are made about
    fixed frame rates – timestamps drive all temporal calculations.
    """

    def __init__(self, config: TemporalRiskConfig | None = None):
        self.cfg = config or TemporalRiskConfig()
        self._reset_state()
        self._current_eval_status = None
        # Internal accumulators
        self._last_timestamp: Optional[float] = None
        self._alert_event: Optional[Dict[str, Any]] = None

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def process(
        self,
        *,
        timestamp: float,
        label: str,
        probabilities: Optional[Dict[str, float]] = None,
        confidence: Optional[float] = None,
        viewpoint: Optional[str] = None,
        tracking_state: Optional[str] = None,
        pose_valid: Optional[bool] = None,
        sitting_state: Optional[bool] = None,
        invalid_state: Optional[str] = None,
        posture_evaluation: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Consume a single observation."""
        if invalid_state and invalid_state in self.cfg.invalid_states:
            self._handle_invalid_state(timestamp, invalid_state)
            return None

        if confidence is None:
            if probabilities:
                confidence = max(probabilities.values())
            else:
                confidence = 1.0

        raw_risk = self.cfg.risk_mapping.get(label, 0.0) * confidence
        # Incorporate derived rule-based posture evidence (head tilt, shoulder misalignment, trunk tilt)
        eval_status = posture_evaluation.get("overall_status") if posture_evaluation else None
        if eval_status == "BAD":
            raw_risk = max(raw_risk, 0.95)
        elif eval_status == "MODERATE":
            raw_risk = max(raw_risk, 0.45)
        # Store current ergonomic evaluation for later use in state updates
        self._current_eval_status = eval_status
        # Reset timer if posture is not BAD to avoid lingering accumulation
        if eval_status != "BAD":
            self._risky_start_ts = None


        # Continuous temporal accumulation based on elevated risk threshold
        if raw_risk >= self.cfg.risk_threshold:
            if self._risky_start_ts is None:
                self._risky_start_ts = timestamp
            self._stable_start_ts = None
        else:
            if self._stable_start_ts is None:
                self._stable_start_ts = timestamp

        self._update_state(timestamp, raw_risk)

        event = None
        if self.state == RiskState.ACTIVE_RISK and not self._in_cooldown:
            event = self._create_alert(timestamp, label, raw_risk, viewpoint, posture_evaluation)
            self._enter_cooldown(timestamp)

        if event is not None:
            self._alert_event = event
        # Update previous evaluation status after handling event
        self._prev_eval_status = getattr(self, "_current_eval_status", None)
        return event

    # ---------------------------------------------------------------------
    # Internal helpers – keep them private to maintain a clean public API
    # ---------------------------------------------------------------------
    def _reset_state(self):
        self.state = RiskState.NORMAL
        self._current_label: Optional[str] = None
        self._risky_start_ts: Optional[float] = None
        self._stable_start_ts: Optional[float] = None
        self._cooldown_end_ts: Optional[float] = None
        self._in_cooldown = False
        # Track previous ergonomic evaluation status to manage timer resets
        self._prev_eval_status: Optional[str] = None
        self._alert_event = None

    def _handle_invalid_state(self, timestamp: float, invalid_state: str):
        if self.state == RiskState.ACTIVE_RISK:
            pass
        if self._cooldown_end_ts and timestamp < self._cooldown_end_ts:
            self._in_cooldown = True
        else:
            self._in_cooldown = False

    def _update_state(self, ts: float, raw_risk: float):
        # Track previous ergonomic evaluation to manage timer resets
        # Handle cooldown first
        if self._cooldown_end_ts and ts < self._cooldown_end_ts:
            self._in_cooldown = True
            self.state = RiskState.COOLDOWN
            return
        else:
            self._in_cooldown = False
            self._cooldown_end_ts = None
            self.state = RiskState.NORMAL

        # Determine which persistence duration to use based on ergonomic evaluation
        # Determine persistence duration based on current ergonomic evaluation
        # Choose persistence duration: use bad_persistence if BAD and set, otherwise default
        persistence_needed = (
            self.cfg.bad_persistence_duration
            if getattr(self, "_current_eval_status", None) == "BAD" and self.cfg.bad_persistence_duration is not None
            else self.cfg.persistence_duration
        )
        # If evaluation just switched to BAD, reset the risky start timestamp to start fresh
        if getattr(self, "_current_eval_status", None) == "BAD" and getattr(self, "_prev_eval_status", None) != "BAD":
            self._risky_start_ts = None

        if raw_risk >= self.cfg.risk_threshold:
            if self._risky_start_ts is not None:
                duration = ts - self._risky_start_ts
                if duration >= persistence_needed:
                    self.state = RiskState.ACTIVE_RISK
                else:
                    self.state = RiskState.WATCH if raw_risk >= self.cfg.watch_threshold else RiskState.NORMAL
            else:
                self._risky_start_ts = ts
                self.state = RiskState.WATCH if raw_risk >= self.cfg.watch_threshold else RiskState.NORMAL
        else:
            # Reset risky start when risk falls below threshold
            self._risky_start_ts = None
            if self.state in {RiskState.ACTIVE_RISK, RiskState.WATCH, RiskState.NORMAL}:
                if self.state != RiskState.NORMAL:
                    if self._stable_start_ts is None:
                        self._stable_start_ts = ts
                        self.state = RiskState.RECOVERING
                    else:
                        stable_dur = ts - self._stable_start_ts
                        if stable_dur >= self.cfg.recovery_duration:
                            self.state = RiskState.NORMAL
                            self._stable_start_ts = None
                        else:
                            self.state = RiskState.RECOVERING
            else:
                pass  # No action needed

    def _enter_cooldown(self, ts: float):
        # Reset previous evaluation status when entering cooldown to avoid stale BAD timer
        self._prev_eval_status = getattr(self, "_current_eval_status", None)
        self._cooldown_end_ts = ts + self.cfg.cooldown_duration
        self._in_cooldown = True
        self.state = RiskState.COOLDOWN
        self._risky_start_ts = None
        self._stable_start_ts = None

    def _create_alert(
        self,
        ts: float,
        label: str,
        risk_score: float,
        viewpoint: Optional[str] = None,
        posture_evaluation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build structured alert event with exact user-facing message wording."""
        message = "You're compromising with your posture. Please correct your posture."
        voice_msg = message

        alert_type = f"PERSISTENT_{label}"
        if posture_evaluation:
            head_st = posture_evaluation.get("head", {}).get("status")
            shoulder_st = posture_evaluation.get("shoulder", {}).get("status")
            trunk_st = posture_evaluation.get("trunk", {}).get("status")
            if head_st == "BAD":
                alert_type = "PERSISTENT_HEAD_TILT"
            elif shoulder_st == "BAD":
                alert_type = "PERSISTENT_SHOULDER_MISALIGNMENT"
            elif trunk_st == "BAD":
                alert_type = "PERSISTENT_TRUNK_MISALIGNMENT"

        event: Dict[str, Any] = {
            "timestamp": ts,
            "posture": label,
            "risk_score": round(risk_score, 3),
            "risk_level": "ALERT",
            "alert_type": alert_type,
            "message": message,
            "voice_message": voice_msg,
            "viewpoint": viewpoint,
            "risk_state": self.state.value,
        }
        return event

    # ---------------------------------------------------------------------
    # Utility for external callers – expose current internal diagnostics
    # ---------------------------------------------------------------------
    def get_debug_state(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "current_label": self._current_label,
            "risky_start_ts": self._risky_start_ts,
            "stable_start_ts": self._stable_start_ts,
            "cooldown_end_ts": self._cooldown_end_ts,
            "in_cooldown": self._in_cooldown,
        }

# -------------------------------------------------------------------------
# Simple sanity‑check when the module is run directly
# -------------------------------------------------------------------------
if __name__ == "__main__":
    cfg = TemporalRiskConfig(persistence_duration=15.0)
    engine = TemporalRiskEngine(cfg)
    start = time.time()
    # Simulate 20 seconds of forward lean (high confidence)
    for i in range(0, 21, 5):
        engine.process(
            timestamp=start + i,
            label="TLF",
            probabilities={"TLF": 0.92, "TUP": 0.08},
        )
    # One more step after alert to see cooldown
    engine.process(timestamp=start + 22, label="TLF", probabilities={"TLF": 0.95})
    print("Final debug state:", engine.get_debug_state())
