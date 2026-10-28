// src/components/PostureStatus.jsx
import React from 'react';
import { getPostureLabel, get3StatePosture } from '../utils/postureLabels';

export default function PostureStatus({ posture, confidence, riskLevel, temporalState, postureEvaluation }) {
  const threeState = get3StatePosture(posture, riskLevel, temporalState, postureEvaluation);
  const detailLabel = getPostureLabel(posture);
  const confidencePct = confidence != null ? `${(confidence * 100).toFixed(0)}%` : '—';

  const head = postureEvaluation?.head;
  const shoulder = postureEvaluation?.shoulder;
  const trunk = postureEvaluation?.trunk;

  const getStatusBadge = (status) => {
    if (status === 'GOOD') return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    if (status === 'MODERATE') return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    if (status === 'BAD') return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    return 'bg-slate-800 text-slate-400 border-slate-700';
  };

  return (
    <div className="p-5 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Posture Classification
        </span>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border flex items-center space-x-1.5 ${threeState.badgeBg}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${threeState.dotColor}`} />
          <span>{threeState.status}</span>
        </span>
      </div>

      <div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold tracking-tight" style={{ color: threeState.accentColor }}>
            {threeState.status}
          </span>
          {posture && (
            <span className="text-sm font-medium text-slate-400">
              ({detailLabel})
            </span>
          )}
        </div>
        <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
          <span>{threeState.description}</span>
          {confidence != null && (
            <span className="text-cyan-400 font-mono font-semibold ml-2">
              {confidencePct}
            </span>
          )}
        </div>
      </div>

      {/* Head, Shoulder & Trunk Rule-Based Alignment Status Badges */}
      {postureEvaluation && (
        <div className="pt-2 border-t border-slate-800/80 space-y-1.5 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 font-medium">Head Posture:</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(head?.status)}`}>
              {head?.status || 'GOOD'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400 font-medium">Shoulder Posture:</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(shoulder?.status)}`}>
              {shoulder?.status || 'GOOD'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400 font-medium">Trunk Posture:</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(trunk?.status)}`}>
              {trunk?.status || 'GOOD'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

