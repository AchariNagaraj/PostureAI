import dataclasses
from typing import Optional, Set, Dict, Any

@dataclasses.dataclass
class TemporalRiskConfig:
    """Central configuration for the research‑grade temporal risk engine.

    All fields are engineering parameters and may be tuned experimentally.
    """
    persistence_duration: float = 5.0   # seconds a risky posture must persist before alert
    recovery_duration: float = 5.0      # seconds of stable low‑risk posture before returning to NORMAL
    cooldown_duration: float = 20.0     # seconds after an alert during which no new alerts are emitted
    bad_persistence_duration: Optional[float] = None  # Override BAD persistence, defaults to persistence_duration
    risk_mapping: Dict[str, float] = dataclasses.field(default_factory=lambda: {
        "TUP": 0.0,
        "TLB": 0.5,
        "TLF": 1.0,
        "TLL": 1.0,
        "TLR": 1.0,
    })
    risk_threshold: float = 0.5          # risk_score above which ACTIVE_RISK is considered
    watch_threshold: float = 0.2         # risk_score above which WATCH level is triggered
    risk_labels: Set[str] = dataclasses.field(default_factory=lambda: {"TLB", "TLF", "TLL", "TLR"})
    invalid_states: Set[str] = dataclasses.field(default_factory=lambda: {
        "NO_PERSON",
        "MULTIPLE_PEOPLE",
        "TARGET_LOST",
        "POSE_FAILURE",
        "UNKNOWN_VIEWPOINT",
        "INVALID_POSE",
    })
    voice_enabled: bool = True           # toggle voice message generation in alerts
    # Additional fields can be added later without breaking existing code
