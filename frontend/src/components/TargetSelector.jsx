// src/components/TargetSelector.jsx
import React from 'react';
import { getTrackingStateLabel } from '../utils/postureLabels';

export default function TargetSelector({
  personState,
  trackingState,
  targetId,
  candidates = [],
  onSelectTarget,
  onChangeTarget,
}) {
  const display = getTrackingStateLabel(trackingState);
  const isMultiple = personState === 'MULTIPLE_PEOPLE' || trackingState === 'AWAITING_SELECTION';
  const isLost = trackingState === 'TARGET_LOST' || trackingState === 'TEMPORARILY_LOST' || trackingState === 'AWAITING_CONFIRMATION';
  const isTracking = trackingState === 'TARGET_TRACKING' && targetId != null;

  let badgeColor = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
  if (isMultiple) badgeColor = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  if (isLost) badgeColor = 'bg-rose-500/10 text-rose-400 border-rose-500/30';

  return (
    <div className="p-4 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Person Tracking Subsystem
        </div>
        {isTracking && onChangeTarget && (
          <button
            onClick={onChangeTarget}
            className="px-2.5 py-1 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg border border-slate-700 transition"
          >
            Change Person
          </button>
        )}
      </div>

      <div className="flex items-center space-x-2">
        <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold border ${badgeColor}`}>
          {display}
        </span>
        {targetId && (
          <span className="px-2 py-0.5 rounded-md bg-cyan-950 text-cyan-300 border border-cyan-800/60 text-xs font-mono font-medium">
            Person ID #{targetId}
          </span>
        )}
      </div>

      {/* Interactive candidate list or continue confirmation prompt */}
      {candidates && candidates.length > 0 && (isMultiple || isLost) && (
        <div className="pt-2 border-t border-slate-800/80 space-y-2">
          <p className="text-xs text-slate-300 font-medium">
            {isMultiple
              ? 'Multiple people detected. Click candidate below or tap candidate box on camera:'
              : 'Target detected. Confirm person to resume monitoring:'}
          </p>
          <div className="flex flex-col gap-2">
            {candidates.map((cand) => (
              <div key={cand.temp_id} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
                <div>
                  <span className="font-semibold text-white">Person #{cand.temp_id}</span>
                  {cand.is_target && <span className="ml-2 text-[10px] text-cyan-400 font-mono">(Previously Locked)</span>}
                </div>
                <button
                  onClick={() => {
                    if (cand.is_target && onChangeTarget) {
                      onChangeTarget(); // Reset tracking before continuing
                    }
                    onSelectTarget && onSelectTarget(cand.temp_id);
                  }}
                  className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded-lg text-xs transition shadow-sm"
                >
                  {cand.is_target ? 'Continue Monitoring' : 'Select & Monitor'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

