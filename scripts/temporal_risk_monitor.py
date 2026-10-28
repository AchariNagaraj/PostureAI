# scripts/temporal_risk_monitor.py
"""Temporal risk monitoring utilities for PostureAI.

- Provides a `RiskMonitor` class that tracks posture predictions over time.
- Emits alerts when a risky posture (non‑upright) exceeds a configurable duration.
- Can be integrated into the webcam inference pipeline or used in batch mode.
"""

import time
from typing import Callable, Iterable, Tuple

DEFAULT_MAX_DURATION = 30.0  # seconds
RISK_LABELS = {"TLB", "TLF", "TLR", "TLL"}

class RiskMonitor:
    """Monitor a stream of (timestamp, label) and trigger callbacks on risk.

    Parameters
    ----------
    max_duration: float
        Maximum allowed duration (seconds) for a risky posture before alert.
    risk_labels: set[str]
        Labels considered risky. Defaults to the four leaning classes.
    alert_callback: Callable[[str, float], None]
        Function called with (label, elapsed_seconds) when risk is exceeded.
    """

    def __init__(self, max_duration: float = DEFAULT_MAX_DURATION,
                 risk_labels: set = RISK_LABELS,
                 alert_callback: Callable[[str, float], None] = None):
        self.max_duration = max_duration
        self.risk_labels = risk_labels
        self.alert_callback = alert_callback or self._default_alert
        self._reset_state()

    def _reset_state(self):
        self.current_label = None
        self.start_time = None

    def _default_alert(self, label: str, elapsed: float):
        print(f"[ALERT] {label} held for {elapsed:.1f}s (>{self.max_duration}s)")

    def process(self, timestamp: float, label: str):
        """Feed a new observation into the monitor.

        Parameters
        ----------
        timestamp: float
            Seconds since epoch (e.g., ``time.time()``).
        label: str
            Predicted posture label.
        """
        if label != self.current_label:
            self.current_label = label
            self.start_time = timestamp
            return
        if label in self.risk_labels:
            elapsed = timestamp - self.start_time
            if elapsed >= self.max_duration:
                self.alert_callback(label, elapsed)

    def run_stream(self, stream: Iterable[Tuple[float, str]]):
        """Convenience method to process an iterable of (ts, label)."""
        for ts, lbl in stream:
            self.process(ts, lbl)

if __name__ == "__main__":
    monitor = RiskMonitor(max_duration=30)
    start = time.time()
    simulated = [(start + i, "TLB") for i in range(0, 36, 5)]
    monitor.run_stream(simulated)
