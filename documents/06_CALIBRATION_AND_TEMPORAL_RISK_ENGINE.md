# PostureAI — Personal Calibration & Temporal Risk Engine

**Document Code:** `DOC-06-RISK`  
**Relative Path:** `documents/06_CALIBRATION_AND_TEMPORAL_RISK_ENGINE.md`  
**Calibration Engine:** Robust Median Baseline Normalizer (`CalibrationBaseline`)  
**Risk Engine:** Continuous Temporal State Machine (`TemporalRiskEngine`)  
**Alert Throttling:** Multi-Stage Hysteresis & Cooldown Suppression  

---

## 1. The Need for Personal Calibration

A fundamental reason off-the-shelf ergonomic software fails in practice is the **"One-Size-Fits-All" fallacy**:
1. **Natural Anatomical Variations:** Human spines naturally exhibit varying degrees of thoracic kyphosis and cervical lordosis. A person with a natural $8^\circ$ forward cervical tilt is not necessarily experiencing strain if that represents their comfortable, relaxed baseline.
2. **Camera Placement Discrepancies:** A webcam placed at eye-level produces an entirely different default camera-to-eye angle than a webcam integrated into a laptop resting on a desk surface angled upward.
3. **Desk & Display Geometry:** Variations in desk height, chair depth, and external monitor elevation shift the neutral reference point across different workstations.

```text
STATIC THRESHOLDS (Rigid)                    PERSONAL CALIBRATION (Adaptive)
Fixed rule: "Pitch > 15° = BAD"              Rule: "|Pitch - Personal_Baseline| > 15° = BAD"
      |                                                    |
      v                                                    v
False positive on tall users;                Adapts to user's body & workstation;
False alarms due to low webcams.             Measures true deviation from comfortable neutral.
```

---

## 2. The Calibration Protocol (`CalibrationBaseline`)

The calibration subsystem is implemented in `ml/inference/feature_extractor.py`:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as Browser UI (LiveMonitor)
    participant WS as WebSocket Handler (/ws)
    participant Engine as InferenceEngine
    participant Calib as CalibrationBaseline

    User->>Frontend: Clicks "Start Calibration"
    Frontend->>WS: {"type": "START_CALIBRATION"}
    WS->>Engine: start_calibration()
    Engine->>Calib: reset()
    WS-->>Frontend: {"type": "CALIBRATION_STATE", "status": "CALIBRATING"}
    
    loop 10-Second Countdown (Valid Frames Ingestion)
        Frontend->>WS: {"type": "FRAME", ...}
        WS->>Engine: process()
        Engine->>Calib: add_sample(landmarks, pose_valid)
        Note over Calib: Filters NaN / Inf; Appends valid sample dict
    end

    Frontend->>WS: {"type": "FINALIZE_CALIBRATION"}
    WS->>Engine: finalize_calibration()
    Engine->>Calib: finalize()
    Note over Calib: Computes median for each feature axis
    WS-->>Frontend: {"type": "CALIBRATION_STATE", "status": "CALIBRATION_COMPLETE", "info": {...}}
    Note over Engine: Performs complete temporal risk reset
```

### 2.1 Sample Validation & Rejection Criteria
During calibration, candidate frames must satisfy strict quality checks (`add_sample`):
* `pose_valid == True` and landmark count $\ge 25$.
* All extracted biomechanical scalar features must be finite ($\text{NaN}$ and $\pm\infty$ rejected).
* Minimum threshold: A minimum of $\text{MIN\_CALIBRATION\_SAMPLES} = 5$ valid frames is strictly enforced. If fewer than 5 valid frames are captured (e.g., user stepped away), calibration fails with an informative error message.

### 2.2 Robust Median Aggregation
Rather than computing an arithmetic mean—which is vulnerable to sudden single-frame twitches or blinks—the neutral baseline is computed using the **statistical median** across all collected samples:
$$\mathbf{B}_{\text{neutral}}[k] = \operatorname{median}\left(\{s_i[k]\}_{i=1}^N\right) \quad \text{for } k \in \{\text{head\_pitch}, \text{head\_roll}, \text{torso\_pitch}, \text{torso\_lateral\_tilt}, \text{shoulder\_asymmetry}\}$$

---

## 3. Relative Deviation vs Absolute Fallback Evaluation

Once calibrated, all ergonomic rule checks evaluate the **relative deviation** from the user's personal baseline using shortest angular distance math (`_angle_diff`):
$$\Delta\theta = |(\theta_{\text{current}} - \theta_{\text{baseline}} + 180^\circ) \bmod 360^\circ - 180^\circ|$$

### 3.1 Threshold Comparison Table
The system defines two sets of thresholds (`evaluate_posture_rules`):

| Anatomical Dimension | Calibrated Deviation Thresholds | Uncalibrated Absolute Fallback Thresholds |
| :--- | :--- | :--- |
| **Head Roll (Tilt)** | **BAD:** $> 20.0^\circ$ \| **MODERATE:** $> 7.0^\circ$ | **BAD:** $> 22.0^\circ$ \| **MODERATE:** $> 8.0^\circ$ |
| **Head Pitch (Flexion)** | **BAD:** $> 25.0^\circ$ \| **MODERATE:** $> 10.0^\circ$ | **BAD:** $> 30.0^\circ$ \| **MODERATE:** $> 12.0^\circ$ |
| **Trunk Pitch (Slouch)** | **BAD:** $> 25.0^\circ$ \| **MODERATE:** $> 10.0^\circ$ | **BAD:** $> 30.0^\circ$ \| **MODERATE:** $> 12.0^\circ$ |
| **Trunk Lateral Tilt** | **BAD:** $> 20.0^\circ$ \| **MODERATE:** $> 8.0^\circ$ | **BAD:** $> 20.0^\circ$ \| **MODERATE:** $> 10.0^\circ$ |
| **Shoulder Asymmetry** | **BAD:** $> 0.25$ \| **MODERATE:** $> 0.10$ | **BAD:** $> 0.30$ \| **MODERATE:** $> 0.12$ |

### 3.2 Consensus Decision Logic
To eliminate single-sensor jitter, PostureAI enforces a multi-signal consensus rule:
```python
statuses = [head_status, shoulder_status, trunk_status]
bad_count = statuses.count("BAD")
mod_count = statuses.count("MODERATE")

if bad_count >= 2 or (bad_count == 1 and mod_count >= 1):
    overall_status = "BAD"
elif bad_count == 1 or mod_count >= 1:
    overall_status = "MODERATE"
else:
    overall_status = "GOOD"
```

---

## 4. The Research-Grade Temporal Risk Engine

The `TemporalRiskEngine` (`ml/risk/temporal_risk_engine.py`) transforms instantaneous frame predictions into stable, clinically meaningful ergonomic risk states.

```text
                                TEMPORAL RISK STATE MACHINE
                                
   +-------------------------------------------------------------------------------+
   |                                                                               |
   |              +------------------- [NORMAL] <-------------------+              |
   |              |                       |                         |              |
   |              | risk < 0.2            | risk >= 0.2             |              |
   |              |                       v                         |              |
   |              |                    [WATCH]                      |              |
   |              |                       |                         |              |
   |              |                       | risk >= 0.5 for >= 3s   |              |
   |              |                       v                         |              |
   |              |                 [ACTIVE_RISK]                   |              |
   |              |                       |                         |              |
   |              |                       | Emit Alert + Voice      |              |
   |              |                       v                         |              |
   |              |                  [COOLDOWN] (20s lock)          |              |
   |              |                       |                         |              |
   |              |                       | Cooldown expires        |              |
   |              |                       v                         |              |
   |              +----------------- [RECOVERING] ------------------+              |
   |                                 (Stable low risk for 5s)                      |
   |                                                                               |
   +-------------------------------------------------------------------------------+
```

### 4.1 Posture-to-Risk Mapping
Each supervised ML class is mapped to a base ergonomic severity value:
$$\text{Base Risk}(\text{TUP}) = 0.0, \quad \text{Base Risk}(\text{TLB}) = 0.5, \quad \text{Base Risk}(\text{TLF, TLL, TLR}) = 1.0$$
The raw risk score incorporates model confidence:
$$\text{Raw Risk} = \text{Base Risk}(\text{Class}) \times \text{Confidence}$$

If rule-based evaluation indicates severe anatomical misalignment, raw risk is elevated:
* If $\text{overall\_status} == \text{"BAD"}$, $\text{Raw Risk} = \max(\text{Raw Risk}, 0.95)$
* If $\text{overall\_status} == \text{"MODERATE"}$, $\text{Raw Risk} = \max(\text{Raw Risk}, 0.45)$

### 4.2 Temporal Filtering Parameters (`TemporalRiskConfig`)
* **Persistence Duration (`persistence_duration = 3.0s`):** A hazardous posture must be held continuously for at least 3 seconds before the system transitions from `WATCH` to `ACTIVE_RISK`. This guarantees that casual movements (e.g., reaching for a pen or nodding) **never trigger false alarms**.
* **Cooldown Duration (`cooldown_duration = 20.0s`):** Once an alert is fired, the engine enters `COOLDOWN`. No further audible alerts will sound for 20 seconds, preventing alert fatigue while the user adjusts their posture.
* **Recovery Duration (`recovery_duration = 5.0s`):** To transition out of an elevated risk state back to `NORMAL`, the user must maintain a healthy upright posture continuously for 5 seconds.

---

## 5. Multi-Modal Alert Generation

When the state machine enters `ACTIVE_RISK` outside cooldown, it constructs a structured alert event:

```json
{
  "timestamp": 1793145620.142,
  "posture": "TLF",
  "risk_score": 0.95,
  "risk_level": "ALERT",
  "temporal_state": "ACTIVE_RISK",
  "viewpoint": "FRONT",
  "alert_type": "RISK_ALERT",
  "message": "Trunk leaning forward detected — please adjust your posture.",
  "voice_message": "Trunk misaligned, please sit upright.",
  "recommendation": "Straighten your back and align your head over your shoulders.",
  "pose_landmarks": [...]
}
```

### 5.1 The 3-State Application Level Mapping
For end-user clarity on dashboard cards and status badges (`postureLabels.js`), complex internal metrics are synthesized into three intuitive user-facing states:
* **`GOOD` (Green):** Neutral upright posture, normal risk score, stable spinal alignment.
* **`MODERATE` (Orange):** Mild deviation detected, `WATCH` state, or system in `RECOVERING`/`COOLDOWN`.
* **`BAD` (Red):** Sustained non-neutral posture (`ACTIVE_RISK`), prompting immediate corrective action.
