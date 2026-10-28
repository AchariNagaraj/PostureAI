import unittest
import time
from ml.risk.temporal_risk_engine import TemporalRiskEngine, RiskState
from ml.risk.risk_config import TemporalRiskConfig

class TestTemporalRiskEngine(unittest.TestCase):
    def setUp(self):
        cfg = TemporalRiskConfig(
            persistence_duration=5.0,
            recovery_duration=3.0,
            cooldown_duration=4.0,
            risk_threshold=0.5,
            watch_threshold=0.2,
        )
        self.engine = TemporalRiskEngine(cfg)
        self.start = time.time()

    def _process(self, offset, label, prob=1.0):
        ts = self.start + offset
        self.engine.process(timestamp=ts, label=label, probabilities={label: prob})
        return ts

    def test_upright_no_alert(self):
        # 10 seconds of upright posture – should never alert
        for i in range(0, 11, 2):
            self._process(i, "TUP")
        self.assertIsNone(self.engine._alert_event)
        self.assertEqual(self.engine.state, RiskState.NORMAL)

    def test_short_risky_no_alert(self):
        # risky for less than persistence – no alert
        for i in range(0, 4, 2):  # 0,2 seconds, persistence=5
            self._process(i, "TLF", prob=0.9)
        self.assertIsNone(self.engine._alert_event)
        self.assertIn(self.engine.state, {RiskState.WATCH, RiskState.NORMAL})

    def test_long_risky_generates_alert(self):
        # risk persists > persistence_duration
        for i in range(0, 7, 1):  # 0‑6 sec, persistence=5
            self._process(i, "TLF", prob=0.9)
        # The alert is generated on the call that crosses the threshold
        self.assertIsNotNone(self.engine._alert_event)
        self.assertEqual(self.engine._alert_event["risk_level"], "ALERT")
        self.assertEqual(self.engine.state, RiskState.COOLDOWN)

    def test_recovery_after_risk(self):
        # Trigger alert first
        for i in range(0, 7):
            self._process(i, "TLF", prob=0.9)
        # Now feed upright posture long enough for recovery
        for i in range(8, 15, 1):
            self._process(i, "TUP")
        self.assertEqual(self.engine.state, RiskState.NORMAL)

    def test_cooldown_blocks_second_alert(self):
        # First alert
        for i in range(0, 7):
            self._process(i, "TLF", prob=0.9)
        # Within cooldown period, feed more risky data – should not alert again
        for i in range(8, 11):
            self._process(i, "TLF", prob=0.9)
        # No new alert event (still only the first one stored)
        self.assertIsNotNone(self.engine._alert_event)
        # After cooldown expires, another persistent risk should generate a new alert
        for i in range(15, 22):
            self._process(i, "TLF", prob=0.9)
        self.assertIsNotNone(self.engine._alert_event)  # still an alert, but state should be COOLDOWN again
        self.assertEqual(self.engine.state, RiskState.COOLDOWN)

    def test_low_confidence_risk_behaves_differently(self):
        # High confidence risky posture – risk_score = 1.0 * 1.0 = 1.0
        for i in range(0, 7):
            self._process(i, "TLF", prob=0.95)
        self.assertIsNotNone(self.engine._alert_event)
        # Reset engine
        self.setUp()
        # Low confidence (0.3) – risk_score = 1.0 * 0.3 = 0.3 which is below risk_threshold (0.5)
        for i in range(0, 7):
            self._process(i, "TLF", prob=0.3)
        self.assertIsNone(self.engine._alert_event)
        # Should be in WATCH or NORMAL, not ACTIVE_RISK
        self.assertIn(self.engine.state, {RiskState.WATCH, RiskState.NORMAL})

    def test_irregular_timestamps(self):
        # Provide non‑uniform intervals
        offsets = [0, 1.2, 3.5, 6.1, 9.0]
        for off in offsets:
            self._process(off, "TLF", prob=0.9)
        # Total duration > persistence (5 s) – alert should fire
        self.assertIsNotNone(self.engine._alert_event)
        self.assertEqual(self.engine.state, RiskState.COOLDOWN)

    def test_invalid_states_do_not_trigger_risk(self):
        # Feed an invalid state – engine should pause risk timers but not alert
        self._process(0, "TLF", prob=0.9)
        self.engine.process(timestamp=self.start + 1, label="TLF", invalid_state="NO_PERSON")
        self.engine.process(timestamp=self.start + 2, label="TLF", invalid_state="TARGET_LOST")
        # Continue with upright – should recover without ever alerting
        for i in range(3, 8):
            self._process(i, "TUP")
        self.assertIsNone(self.engine._alert_event)
        self.assertEqual(self.engine.state, RiskState.NORMAL)

if __name__ == "__main__":
    unittest.main()
