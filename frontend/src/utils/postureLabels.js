// src/utils/postureLabels.js

export const POSTURE_CLASS_MAP = {
  TUP: 'Upright',
  TLF: 'Trunk Pitch Tilt',
  TLB: 'Trunk Backward Tilt',
  TLL: 'Left Lean',
  TLR: 'Right Lean',
};

export const POSTURE_FULL_MAP = {
  TUP: 'Upright Trunk',
  TLF: 'Trunk Pitch Tilt',
  TLB: 'Trunk Backward Tilt',
  TLL: 'Trunk Leaning Left',
  TLR: 'Trunk Leaning Right',
};

export function getPostureLabel(code) {
  if (!code) return '—';
  return POSTURE_CLASS_MAP[code] || code;
}

export function getPostureFullLabel(code) {
  if (!code) return '—';
  return POSTURE_FULL_MAP[code] || code;
}

export const RISK_LEVEL_CONFIG = {
  NORMAL: {
    label: 'Normal',
    badgeBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    dotColor: 'bg-emerald-500',
    accentColor: '#10B981',
    description: 'Your current posture appears stable.',
  },
  WATCH: {
    label: 'Watch',
    badgeBg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    dotColor: 'bg-amber-500',
    accentColor: '#F59E0B',
    description: 'Your posture has remained outside the neutral range.',
  },
  ACTIVE_RISK: {
    label: 'Active Risk',
    badgeBg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    dotColor: 'bg-rose-500',
    accentColor: '#F43F5E',
    description: 'Consider adjusting your sitting position.',
  },
  RECOVERING: {
    label: 'Recovering',
    badgeBg: 'bg-sky-500/10 text-sky-400 border-sky-500/30',
    dotColor: 'bg-sky-500',
    accentColor: '#38BDF8',
    description: 'Posture returning towards neutral position.',
  },
  COOLDOWN: {
    label: 'Cooldown',
    badgeBg: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
    dotColor: 'bg-zinc-500',
    accentColor: '#71717A',
    description: 'System in observation cooldown.',
  },
};

export function getRiskLevelConfig(level) {
  return RISK_LEVEL_CONFIG[level] || {
    label: level || '—',
    badgeBg: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
    dotColor: 'bg-slate-500',
    accentColor: '#64748B',
    description: 'Monitoring position.',
  };
}

export const VIEWPOINT_MAP = {
  FRONT: 'Front View',
  LEFT_3_4: 'Left 3/4 View',
  RIGHT_3_4: 'Right 3/4 View',
  LEFT_PROFILE: 'Left Profile',
  RIGHT_PROFILE: 'Right Profile',
  UNKNOWN: 'Viewpoint Uncertain',
};

export function getViewpointLabel(vp) {
  if (!vp) return '—';
  return VIEWPOINT_MAP[vp] || vp;
}

export const TRACKING_STATE_MAP = {
  NO_PERSON: 'No person detected',
  ONE_PERSON: 'One person detected',
  MULTIPLE_PEOPLE: 'Multiple people detected',
  TARGET_SELECTED: 'Target selected',
  TARGET_LOST: 'Target temporarily lost',
  RESELECT_REQUIRED: 'Target re-selection required',
};

export function getTrackingStateLabel(state) {
  if (!state) return '—';
  return TRACKING_STATE_MAP[state] || state;
}

export function get3StatePosture(posture, riskLevel, temporalState, postureEvaluation) {
  const state = (temporalState || riskLevel || '').toUpperCase();
  const evalStatus = postureEvaluation?.overall_status;

  if (state === 'ACTIVE_RISK' || state === 'ALERT') {
    return {
      status: 'BAD',
      label: 'BAD',
      badgeBg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      dotColor: 'bg-rose-500',
      accentColor: '#EF4444',
      description: "You're compromising with your posture. Please correct your posture.",
    };
  }

  if (evalStatus === 'BAD') {
    return {
      status: 'BAD',
      label: 'BAD',
      badgeBg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      dotColor: 'bg-rose-500',
      accentColor: '#EF4444',
      description: 'Bad posture detected. Maintain posture to evaluate risk duration.',
    };
  }

  if (evalStatus === 'MODERATE' || state === 'WATCH' || state === 'RECOVERING' || state === 'COOLDOWN') {
    return {
      status: 'MODERATE',
      label: 'MODERATE',
      badgeBg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      dotColor: 'bg-amber-500',
      accentColor: '#F97316',
      description: 'Minor posture deviation detected.',
    };
  }

  return {
    status: 'GOOD',
    label: 'GOOD',
    badgeBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    dotColor: 'bg-emerald-500',
    accentColor: '#10B981',
    description: 'Good posture (head straight, trunk straight, shoulder aligned).',
  };
}




