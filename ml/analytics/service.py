# ml/analytics/service.py
"""Phase 9 Analytics Service Layer.

Implements deterministic timestamp-based calculations, posture duration assignment,
gap-filtered posture transition matrix, UTC midnight interval splitting, and critical-point
preserving timeline downsampling.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..persistence import repositories, models
import time
G_MAX = 10.0  # Maximum valid observation gap in seconds


def process_metric_intervals(metrics: List[models.PostureMetric]) -> Dict[str, Any]:
    """Process a pre-sorted list of PostureMetric models using timestamp-interval math.

    Metrics MUST be sorted by (timestamp ASC, id ASC).

    Returns structured statistics:
      - total_observations: int
      - total_observed_duration_seconds: float
      - posture_counts: dict
      - posture_durations: dict
      - temporal_state_durations: dict
      - risk_level_counts: dict
      - transitions: dict
      - daily_durations_utc: dict (keyed by 'YYYY-MM-DD')
    """
    posture_counts = {"TUP": 0, "TLF": 0, "TLB": 0, "TLL": 0, "TLR": 0}
    posture_durations = {"TUP": 0.0, "TLF": 0.0, "TLB": 0.0, "TLL": 0.0, "TLR": 0.0}
    temporal_state_durations = {
        "NORMAL": 0.0,
        "WATCH": 0.0,
        "ACTIVE_RISK": 0.0,
        "RECOVERING": 0.0,
        "COOLDOWN": 0.0,
    }
    risk_level_counts = {"NORMAL": 0, "WATCH": 0, "ALERT": 0}
    transitions: Dict[str, int] = {}
    head_transitions: Dict[str, int] = {}
    shoulder_transitions: Dict[str, int] = {}
    daily_durations_utc: Dict[str, float] = {}
    total_observed_duration = 0.0

    if not metrics:
        return {
            "total_observations": 0,
            "total_observed_duration_seconds": 0.0,
            "posture_counts": posture_counts,
            "posture_durations": posture_durations,
            "temporal_state_durations": temporal_state_durations,
            "risk_level_counts": risk_level_counts,
            "transitions": transitions,
            "daily_durations_utc": daily_durations_utc,
            "duration_reliable": False,
        }

    # Count observations and risk levels
    for m in metrics:
        p = m.posture
        if p in posture_counts:
            posture_counts[p] += 1
        else:
            posture_counts[p] = 1

        rl = m.risk_level
        if rl in risk_level_counts:
            risk_level_counts[rl] += 1
        else:
            risk_level_counts[rl] = 1

    # Interval processing loop
    n = len(metrics)
    for i in range(n - 1):
        m_curr = metrics[i]
        m_next = metrics[i + 1]

        delta_t = m_next.timestamp - m_curr.timestamp
        if delta_t < 0:
            # Out-of-order fallback guard (should not happen if pre-sorted)
            delta_t = 0.0

        if delta_t <= G_MAX:
            # Valid interval – credit duration to posture and temporal_state
            total_observed_duration += delta_t
            p_curr = m_curr.posture
            if p_curr not in posture_durations:
                posture_durations[p_curr] = 0.0
            posture_durations[p_curr] += delta_t

            ts_curr = m_curr.temporal_state
            if ts_curr not in temporal_state_durations:
                temporal_state_durations[ts_curr] = 0.0
            temporal_state_durations[ts_curr] += delta_t

            # Posture transitions: only count if posture changed AND delta_t <= G_MAX
            if p_curr != m_next.posture:
                trans_key = f"{p_curr}->{m_next.posture}"
                transitions[trans_key] = transitions.get(trans_key, 0) + 1

            # Head state transitions
            head_curr = "HEAD_TILT" if p_curr in ("TLF", "TLL", "TLR") else "HEAD_STRAIGHT"
            head_next = "HEAD_TILT" if m_next.posture in ("TLF", "TLL", "TLR") else "HEAD_STRAIGHT"
            if head_curr != head_next:
                h_key = f"{head_curr}->{head_next}"
                head_transitions[h_key] = head_transitions.get(h_key, 0) + 1

            # Shoulder state transitions
            sh_curr = "SHOULDER_MISALIGNED" if p_curr in ("TLL", "TLR") else "SHOULDERS_ALIGNED"
            sh_next = "SHOULDER_MISALIGNED" if m_next.posture in ("TLL", "TLR") else "SHOULDERS_ALIGNED"
            if sh_curr != sh_next:
                s_key = f"{sh_curr}->{sh_next}"
                shoulder_transitions[s_key] = shoulder_transitions.get(s_key, 0) + 1

            # Midnight interval splitting for daily UTC trends
            dt_curr = datetime.fromtimestamp(m_curr.timestamp, tz=timezone.utc)
            dt_next = datetime.fromtimestamp(m_next.timestamp, tz=timezone.utc)

            date_curr_str = dt_curr.strftime("%Y-%m-%d")
            date_next_str = dt_next.strftime("%Y-%m-%d")

            if date_curr_str == date_next_str:
                daily_durations_utc[date_curr_str] = daily_durations_utc.get(date_curr_str, 0.0) + delta_t
            else:
                # Interval crosses UTC midnight – split at midnight
                midnight_dt = datetime(dt_next.year, dt_next.month, dt_next.day, 0, 0, 0, tzinfo=timezone.utc)
                midnight_ts = midnight_dt.timestamp()
                dur1 = max(0.0, midnight_ts - m_curr.timestamp)
                dur2 = max(0.0, m_next.timestamp - midnight_ts)
                daily_durations_utc[date_curr_str] = daily_durations_utc.get(date_curr_str, 0.0) + dur1
                daily_durations_utc[date_next_str] = daily_durations_utc.get(date_next_str, 0.0) + dur2
        else:
            # Unobserved gap (> G_MAX) – NO duration credit, NO transition credit
            pass

    # Final metric m_n duration is strictly 0.0s (no subsequent observation)

    return {
        "total_observations": n,
        "total_observed_duration_seconds": round(total_observed_duration, 3),
        "posture_counts": posture_counts,
        "posture_durations": {k: round(v, 3) for k, v in posture_durations.items()},
        "temporal_state_durations": {k: round(v, 3) for k, v in temporal_state_durations.items()},
        "risk_level_counts": risk_level_counts,
        "transitions": transitions,
        "daily_durations_utc": {k: round(v, 3) for k, v in daily_durations_utc.items()},
        "duration_reliable": n > 1 and total_observed_duration > 0,
    }


def downsample_timeline(
    metrics: List[models.PostureMetric],
    alerts: List[models.Alert],
    max_points: int = 300,
) -> List[Dict[str, Any]]:
    """Downsample metrics timeline ensuring preserved critical points.

    Explicitly preserves:
      - First metric
      - Last metric
      - Posture transition points
      - Temporal state transition points
      - Metric timestamps matching Alert events
    """
    if not metrics:
        return []

    alert_timestamps = {a.timestamp for a in alerts}
    critical_indices = set()
    n = len(metrics)

    # Always keep first and last
    critical_indices.add(0)
    critical_indices.add(n - 1)

    # Identify transitions and alert markers
    for i in range(n):
        m_curr = metrics[i]
        if m_curr.timestamp in alert_timestamps:
            critical_indices.add(i)
        if i > 0:
            m_prev = metrics[i - 1]
            if m_curr.posture != m_prev.posture:
                critical_indices.add(i)
                critical_indices.add(i - 1)
            if m_curr.temporal_state != m_prev.temporal_state:
                critical_indices.add(i)
                critical_indices.add(i - 1)

    selected_indices = sorted(list(critical_indices))

    # Filler sampling if below max_points
    if len(selected_indices) < max_points and n > len(selected_indices):
        needed = max_points - len(selected_indices)
        step = max(1, n // needed)
        for i in range(0, n, step):
            critical_indices.add(i)
        selected_indices = sorted(list(critical_indices))

    # Format output timeline items
    timeline = []
    for idx in selected_indices:
        m = metrics[idx]
        timeline.append({
            "timestamp": m.timestamp,
            "posture": m.posture,
            "confidence": m.confidence,
            "risk_score": m.risk_score,
            "risk_level": m.risk_level,
            "temporal_state": m.temporal_state,
            "viewpoint": m.viewpoint,
            "is_alert_event": m.timestamp in alert_timestamps,
        })
    return timeline


async def get_summary_analytics(db: AsyncSession, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Calculate overall system analytics across all sessions for a user."""
    sessions = await repositories.get_all_sessions(db, user_id=user_id, limit=1000)
    total_sessions = len(sessions)
    completed_sessions = sum(1 for s in sessions if s.status == "COMPLETED")
    active_sessions = sum(1 for s in sessions if s.status == "ACTIVE")

    all_metrics = await repositories.get_metrics_for_session(db, user_id=user_id)
    all_alerts = await repositories.get_alerts_for_session(db, user_id=user_id)

    stats = process_metric_intervals(all_metrics)

    total_duration = stats["total_observed_duration_seconds"]
    tup_duration = stats["posture_durations"].get("TUP", 0.0)

    upright_ratio = (
        round(tup_duration / total_duration, 4) if total_duration > 0 else 0.0
    )

    total_alerts = len(all_alerts)
    alert_freq_per_hour = (
        round(total_alerts / (total_duration / 3600.0), 2)
        if total_duration > 0
        else None
    )

    # Highest observed risky posture (excluding TUP)
    risky_durations = {
        k: v for k, v in stats["posture_durations"].items() if k != "TUP"
    }
    highest_risky_by_duration = (
        max(risky_durations, key=risky_durations.get)
        if risky_durations and max(risky_durations.values()) > 0
        else None
    )

    risky_counts = {
        k: v for k, v in stats["posture_counts"].items() if k != "TUP"
    }
    highest_risky_by_count = (
        max(risky_counts, key=risky_counts.get)
        if risky_counts and max(risky_counts.values()) > 0
        else None
    )

    avg_session_duration = (
        round(total_duration / completed_sessions, 2)
        if completed_sessions > 0
        else 0.0
    )

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "active_sessions": active_sessions,
        "total_observed_duration_seconds": total_duration,
        "average_session_duration_seconds": avg_session_duration,
        "total_alerts": total_alerts,
        "alert_frequency_per_monitoring_hour": alert_freq_per_hour,
        "upright_duration_ratio": upright_ratio,
        "highest_observed_risky_posture_by_duration": highest_risky_by_duration,
        "highest_observed_risky_posture_by_count": highest_risky_by_count,
    }


async def get_posture_analytics(db: AsyncSession, session_id: Optional[int] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Calculate detailed posture & transition analytics."""
    metrics = await repositories.get_metrics_for_session(db, session_id=session_id, user_id=user_id)
    stats = process_metric_intervals(metrics)

    total_obs = stats["total_observations"]
    total_dur = stats["total_observed_duration_seconds"]

    postures_res = {}
    for p_class in ["TUP", "TLB", "TLF", "TLL", "TLR"]:
        cnt = stats["posture_counts"].get(p_class, 0)
        dur = stats["posture_durations"].get(p_class, 0.0)

        pct_cnt = round((cnt / total_obs) * 100.0, 2) if total_obs > 0 else 0.0
        pct_dur = round((dur / total_dur) * 100.0, 2) if total_dur > 0 else 0.0

        postures_res[p_class] = {
            "observation_count": cnt,
            "percentage_by_count": pct_cnt,
            "duration_seconds": dur,
            "percentage_by_duration": pct_dur,
        }

    # Head & Shoulder Ergonomic Posture Breakdown
    tlf_tll_tlr_dur = (
        stats["posture_durations"].get("TLF", 0.0) +
        stats["posture_durations"].get("TLL", 0.0) +
        stats["posture_durations"].get("TLR", 0.0)
    )
    tup_dur = stats["posture_durations"].get("TUP", 0.0)
    tll_tlr_dur = (
        stats["posture_durations"].get("TLL", 0.0) +
        stats["posture_durations"].get("TLR", 0.0)
    )

    head_straight_dur = max(0.0, total_dur - tlf_tll_tlr_dur)
    head_tilt_dur = tlf_tll_tlr_dur
    head_tilt_pct = round((head_tilt_dur / total_dur) * 100.0, 2) if total_dur > 0 else 0.0

    shoulder_aligned_dur = max(0.0, total_dur - tll_tlr_dur)
    shoulder_misaligned_dur = tll_tlr_dur
    shoulder_misaligned_pct = round((shoulder_misaligned_dur / total_dur) * 100.0, 2) if total_dur > 0 else 0.0

    upright_ratio = round(tup_dur / total_dur, 4) if total_dur > 0 else 0.0

    return {
        "total_observation_count": total_obs,
        "total_observed_duration_seconds": total_dur,
        "upright_duration_ratio": upright_ratio,
        "postures": postures_res,
        "transitions": stats["transitions"],
        "head_alignment": {
            "straight_duration_seconds": round(head_straight_dur, 2),
            "tilt_duration_seconds": round(head_tilt_dur, 2),
            "tilt_percentage": head_tilt_pct,
            "straight_percentage": round(100.0 - head_tilt_pct, 2) if total_dur > 0 else 100.0,
            "status": "BAD" if head_tilt_pct > 25.0 else ("MODERATE" if head_tilt_pct > 10.0 else "GOOD"),
            "guidance": "keep your head straight",
        },
        "shoulder_alignment": {
            "aligned_duration_seconds": round(shoulder_aligned_dur, 2),
            "misaligned_duration_seconds": round(shoulder_misaligned_dur, 2),
            "misaligned_percentage": shoulder_misaligned_pct,
            "aligned_percentage": round(100.0 - shoulder_misaligned_pct, 2) if total_dur > 0 else 100.0,
            "status": "BAD" if shoulder_misaligned_pct > 20.0 else ("MODERATE" if shoulder_misaligned_pct > 8.0 else "GOOD"),
            "guidance": "keep shoulders aligned",
        },
        "trunk_alignment": {
            "straight_duration_seconds": round(tup_dur, 2),
            "tup_percentage": round((tup_dur / total_dur) * 100.0, 2) if total_dur > 0 else 0.0,
            "guidance": "keep trunk straight",
        },
        "head_posture": {
            "monitored_features": ["head_pitch", "head_roll", "forward_head_displacement"],
            "guidance": "keep your head straight",
        },
        "shoulder_posture": {
            "monitored_features": ["shoulder_asymmetry"],
            "guidance": "shoulder aligned",
        },
        "trunk_posture": {
            "monitored_features": ["torso_pitch", "torso_lateral_tilt", "torso_rotation"],
            "guidance": "trunk straight",
        },
        "posture_alignment_guidance": "You're compromising with your posture. Please correct your posture.",
    }


async def get_session_analytics_list(db: AsyncSession, user_id: Optional[int] = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Return paginated session summaries with observed statistics."""
    sessions = await repositories.get_all_sessions(db, user_id=user_id, limit=limit, offset=offset)
    total_count = await repositories.get_session_count(db, user_id=user_id)

    results = []
    for s in sessions:
        metrics = await repositories.get_metrics_for_session(db, session_id=s.id, user_id=user_id)
        alerts = await repositories.get_alerts_for_session(db, session_id=s.id, user_id=user_id)
        stats = process_metric_intervals(metrics)

        dur = stats["total_observed_duration_seconds"]

        # Auto-complete inactive sessions that were left open
        if s.status == "ACTIVE":
            last_ts = metrics[-1].timestamp if metrics else s.start_timestamp
            if time.time() - last_ts > 60.0:
                s.status = "COMPLETED"
                s.end_timestamp = last_ts
                await db.commit()

        created_str = (
            s.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            if s.created_at
            else datetime.fromtimestamp(s.start_timestamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        results.append({
            "id": s.id,
            "status": s.status,
            "created_at": created_str,
            "start_timestamp": s.start_timestamp,
            "end_timestamp": s.end_timestamp,
            "observed_duration_seconds": dur,
            "total_observations": stats["total_observations"],
            "total_alerts": len(alerts),
        })

    return {
        "sessions": results,
        "total_count": total_count,
    }


async def get_single_session_detail(db: AsyncSession, session_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Return full metrics timeline, transitions, and alerts for a session."""
    session = await repositories.get_session_by_id(db, session_id, user_id=user_id)
    if not session:
        return None

    metrics = await repositories.get_metrics_for_session(db, session_id=session_id, user_id=user_id)
    alerts = await repositories.get_alerts_for_session(db, session_id=session_id, user_id=user_id)
    stats = process_metric_intervals(metrics)
    timeline = downsample_timeline(metrics, alerts)

    formatted_alerts = [
        {
            "id": a.id,
            "timestamp": a.timestamp,
            "posture": a.posture,
            "risk_score": a.risk_score,
            "risk_level": a.risk_level,
            "alert_type": a.alert_type,
            "message": a.message,
            "voice_message": a.voice_message,
        }
        for a in alerts
    ]

    return {
        "session_id": session.id,
        "status": session.status,
        "start_timestamp": session.start_timestamp,
        "end_timestamp": session.end_timestamp,
        "observed_duration_seconds": stats["total_observed_duration_seconds"],
        "timeline": timeline,
        "alerts": formatted_alerts,
        "transitions": stats["transitions"],
    }


async def get_session_report(db: AsyncSession, session_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Generate structured, non-clinical inspection report payload."""
    detail = await get_single_session_detail(db, session_id, user_id=user_id)
    if not detail:
        return None

    metrics = await repositories.get_metrics_for_session(db, session_id=session_id, user_id=user_id)
    stats = process_metric_intervals(metrics)
    posture_stats = await get_posture_analytics(db, session_id=session_id, user_id=user_id)

    total_dur = stats["total_observed_duration_seconds"]
    tup_dur = stats["posture_durations"].get("TUP", 0.0)
    upright_ratio = round(tup_dur / total_dur, 4) if total_dur > 0 else 0.0

    # Risky posture summary
    risky_durations = {k: v for k, v in stats["posture_durations"].items() if k != "TUP"}
    primary_risky = (
        max(risky_durations, key=risky_durations.get)
        if risky_durations and max(risky_durations.values()) > 0
        else "None"
    )

    total_alerts = len(detail["alerts"])
    total_transitions = sum(stats["transitions"].values())

    # Deterministic non-clinical summary
    summary_text = (
        f"Session #{session_id} recorded {stats['total_observations']} posture observations over "
        f"{total_dur:.1f} seconds of active monitoring. Upright trunk (TUP) posture accounted for "
        f"{upright_ratio * 100:.1f}% of observed duration. "
        f"A total of {total_alerts} persistent risk alerts were generated, and {total_transitions} valid "
        f"posture transitions were recorded. "
        f"The primary non-upright posture observed by duration was {primary_risky}. "
        f"Posture guidance: keep your head straight, trunk straight, shoulder aligned."
    )

    return {
        "session_id": session_id,
        "status": detail["status"],
        "start_timestamp": detail["start_timestamp"],
        "end_timestamp": detail["end_timestamp"],
        "observed_duration_seconds": total_dur,
        "upright_duration_ratio": upright_ratio,
        "primary_risky_posture_by_duration": primary_risky,
        "total_alerts": total_alerts,
        "total_transitions": total_transitions,
        "posture_breakdown": posture_stats["postures"],
        "head_posture": posture_stats["head_posture"],
        "shoulder_posture": posture_stats["shoulder_posture"],
        "trunk_posture": posture_stats["trunk_posture"],
        "posture_alignment_guidance": "keep your head straight, trunk straight, shoulder aligned",
        "transitions": stats["transitions"],
        "temporal_state_durations": stats["temporal_state_durations"],
        "alerts": detail["alerts"],
        "engineering_summary": summary_text,
    }

