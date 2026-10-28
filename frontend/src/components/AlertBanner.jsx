// src/components/AlertBanner.jsx
import React from 'react';
import { AlertIcon, CloseIcon } from './Icons';
import { getPostureLabel } from '../utils/postureLabels';

export default function AlertBanner({ alertEvent, dismiss }) {
  if (!alertEvent) return null;
  const { posture, message, risk_score, alert_type, risk_level } = alertEvent;
  const score = risk_score != null ? risk_score.toFixed(2) : '—';
  const humanPosture = getPostureLabel(posture);

  return (
    <div
      role="alert"
      className="p-4 bg-gradient-to-r from-rose-950/90 via-slate-900 to-rose-950/90 backdrop-blur-md border border-rose-500/50 rounded-2xl shadow-2xl text-white flex items-start justify-between space-x-4 animate-in fade-in slide-in-from-top-2 duration-300"
    >
      <div className="flex items-start space-x-3.5">
        <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400 flex-shrink-0 mt-0.5">
          <AlertIcon className="w-6 h-6 animate-pulse" />
        </div>
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-bold text-rose-200 tracking-tight">Posture Alert</h3>
            {alert_type && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/30">
                {alert_type}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-200 font-medium">
            {message || 'Posture threshold elevated for an extended period.'}
          </p>
          <div className="flex items-center space-x-4 pt-1 text-xs text-slate-400">
            <span><strong>Posture:</strong> <span className="text-white font-semibold">{humanPosture}</span></span>
            <span><strong>Risk Score:</strong> <span className="text-rose-400 font-mono font-bold">{score}</span></span>
            {risk_level && <span><strong>State:</strong> <span className="text-amber-400 font-semibold">{risk_level}</span></span>}
          </div>
        </div>
      </div>

      {dismiss && (
        <button
          onClick={dismiss}
          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800/80 transition flex-shrink-0 focus:outline-none"
          title="Dismiss Alert"
        >
          <CloseIcon className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}
