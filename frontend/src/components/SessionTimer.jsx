// src/components/SessionTimer.jsx
import React, { useEffect, useState } from "react";

export default function SessionTimer({ startTime }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startTime) return;
    const interval = setInterval(() => {
      setElapsed(Date.now() - startTime);
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const format = (ms) => {
    const totalSec = Math.floor(ms / 1000);
    const hrs = Math.floor(totalSec / 3600)
      .toString()
      .padStart(2, "0");
    const mins = Math.floor((totalSec % 3600) / 60)
      .toString()
      .padStart(2, "0");
    const secs = (totalSec % 60).toString().padStart(2, "0");
    return `${hrs}:${mins}:${secs}`;
  };

  return (
    <div className="flex items-center space-x-2 px-3.5 py-1.5 bg-slate-900/90 rounded-xl border border-slate-800 text-xs text-slate-300 shadow-inner">
      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
      <span className="text-slate-400 font-medium">Session Duration:</span>
      <span className="font-mono font-bold text-white tracking-wider">{format(elapsed)}</span>
    </div>
  );
}
