// src/components/RiskIndicator.jsx
import React from 'react';
import { getRiskLevelConfig } from '../utils/postureLabels';

export default function RiskIndicator({ riskScore, riskLevel, temporalState }) {
  const config = getRiskLevelConfig(riskLevel);
  const scoreDisplay = riskScore != null ? riskScore.toFixed(2) : '—';
  const temporalDisplay = temporalState || '—';

  return (
    <div className="p-5 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Risk Assessment
        </span>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border flex items-center space-x-1.5 ${config.badgeBg}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor}`} />
          <span>{config.label}</span>
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 pt-1">
        <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
          <div className="text-[11px] text-slate-400 uppercase font-medium">Risk Score</div>
          <div className="text-xl font-bold text-slate-100 font-mono mt-0.5">{scoreDisplay}</div>
        </div>
        <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
          <div className="text-[11px] text-slate-400 uppercase font-medium">Temporal State</div>
          <div className="text-sm font-semibold text-slate-200 mt-1 truncate">{temporalDisplay}</div>
        </div>
      </div>
    </div>
  );
}
