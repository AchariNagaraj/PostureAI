// src/components/CalibrationCard.jsx
import React from 'react';
import { ShieldIcon } from './Icons';
import { getViewpointLabel, getTrackingStateLabel } from '../utils/postureLabels';

export default function CalibrationCard({
  progress = 0,
  secondsRemaining = 10,
  poseValid = true,
  trackingState = 'TRACKING',
  viewpoint = 'FRONT',
  isComplete = false,
  isFailed = false,
  failReason = '',
  onStartMonitoring,
  onCancel,
  onTryAgain,
}) {
  const viewpointStr = getViewpointLabel(viewpoint);
  const trackingStr = getTrackingStateLabel(trackingState);

  return (
    <div className="p-6 bg-slate-900/95 backdrop-blur-xl rounded-2xl border border-cyan-500/30 shadow-2xl space-y-5 animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <ShieldIcon className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">
              {isComplete ? 'Calibration Complete' : isFailed ? 'Calibration Failed' : "Let's calibrate your posture"}
            </h3>
            <p className="text-xs text-slate-400">
              {isComplete
                ? 'Your baseline sitting geometry has been established.'
                : isFailed
                ? failReason || 'Could not establish stable baseline.'
                : 'Sit naturally in your normal working position for 10 seconds.'}
            </p>
          </div>
        </div>

        {isComplete ? (
          <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold text-xs rounded-full flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>CALIBRATED</span>
          </span>
        ) : isFailed ? (
          <span className="px-3 py-1 bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold text-xs rounded-full">
            FAILED
          </span>
        ) : (
          <span className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono font-bold text-xs rounded-full">
            {secondsRemaining}s REMAINING
          </span>
        )}
      </div>

      {/* Progress Bar Area */}
      {!isComplete && !isFailed && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-semibold text-slate-300">
            <span>CALIBRATING BASELINE...</span>
            <span className="font-mono text-cyan-400">{Math.round(progress)}%</span>
          </div>
          <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800 p-0.5">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full transition-all duration-300 shadow-md shadow-cyan-500/50"
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
        </div>
      )}

      {/* Quality Gate Check Badges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl space-y-1">
          <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Pose Quality</div>
          <div className={`text-xs font-bold ${poseValid ? 'text-emerald-400' : 'text-amber-400'}`}>
            {poseValid ? '✓ Good Quality' : '⚠ Adjust Position'}
          </div>
        </div>

        <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl space-y-1">
          <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Person Detection</div>
          <div className="text-xs font-bold text-cyan-400">
            {trackingStr}
          </div>
        </div>

        <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl space-y-1">
          <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Camera Viewpoint</div>
          <div className="text-xs font-bold text-indigo-400">
            {viewpointStr}
          </div>
        </div>

        <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl space-y-1">
          <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Target Tracking</div>
          <div className="text-xs font-bold text-emerald-400">
            ✓ Stable Tracking
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end space-x-3 pt-2">
        {isComplete ? (
          <button
            onClick={onStartMonitoring}
            className="px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white rounded-xl font-bold text-sm transition-all shadow-lg shadow-emerald-500/25 flex items-center space-x-2"
          >
            <span>Begin Active Monitoring</span>
          </button>
        ) : isFailed ? (
          <>
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-semibold text-xs transition"
            >
              Cancel
            </button>
            <button
              onClick={onTryAgain}
              className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl font-bold text-xs transition shadow-lg shadow-cyan-600/20"
            >
              Try Again
            </button>
          </>
        ) : (
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-semibold text-xs transition"
          >
            Cancel Calibration
          </button>
        )}
      </div>
    </div>
  );
}
