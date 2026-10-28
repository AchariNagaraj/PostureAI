// src/components/ConnectionStatus.jsx
import React from 'react';

export default function ConnectionStatus({ camStatus, wsStatus, monitorState }) {
  const getBadgeStyle = (status, type) => {
    if (status === 'ACTIVE' || status === 'CONNECTED' || status === 'ACTIVE') {
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30Dot bg-emerald-500';
    }
    if (status === 'CONNECTING' || status === 'INITIALIZING' || status === 'STARTING') {
      return 'bg-amber-500/10 text-amber-400 border-amber-500/30Dot bg-amber-500';
    }
    return 'bg-slate-500/10 text-slate-400 border-slate-500/30Dot bg-slate-500';
  };

  const isCamActive = camStatus === 'ACTIVE';
  const isWsConnected = wsStatus === 'CONNECTED';
  const isMonitoring = monitorState === 'ACTIVE';

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      {/* Camera Status */}
      <div className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border ${isCamActive ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-800/80 text-slate-400 border-slate-700/60'}`}>
        <span className={`w-2 h-2 rounded-full ${isCamActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
        <span className="font-medium">Camera:</span>
        <span className="font-semibold">{camStatus || 'Disconnected'}</span>
      </div>

      {/* WebSocket Status */}
      <div className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border ${isWsConnected ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-800/80 text-slate-400 border-slate-700/60'}`}>
        <span className={`w-2 h-2 rounded-full ${isWsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
        <span className="font-medium">WebSocket:</span>
        <span className="font-semibold">{wsStatus || 'Disconnected'}</span>
      </div>

      {/* Monitoring Status */}
      <div className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border ${isMonitoring ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'bg-slate-800/80 text-slate-400 border-slate-700/60'}`}>
        <span className={`w-2 h-2 rounded-full ${isMonitoring ? 'bg-cyan-400 animate-pulse' : 'bg-slate-500'}`} />
        <span className="font-medium">Monitoring:</span>
        <span className="font-semibold">{isMonitoring ? 'Active' : 'Stopped'}</span>
      </div>
    </div>
  );
}
