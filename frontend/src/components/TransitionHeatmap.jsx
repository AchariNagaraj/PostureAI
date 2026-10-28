// src/components/TransitionHeatmap.jsx
import React from 'react';
import { getPostureLabel } from '../utils/postureLabels';

const POSTURES = ['TUP', 'TLF', 'TLB', 'TLL', 'TLR'];

export default function TransitionHeatmap({ transitions = {} }) {
  // Find max count for color scaling
  const maxCount = Math.max(1, ...Object.values(transitions));

  const getHeatmapColor = (count) => {
    if (!count || count === 0) return 'bg-slate-950/80 border-slate-800/60 text-slate-600';
    const ratio = count / maxCount;
    if (ratio > 0.75) return 'bg-cyan-500/30 border-cyan-400/60 text-cyan-300 font-bold shadow-md shadow-cyan-500/20';
    if (ratio > 0.4) return 'bg-teal-500/20 border-teal-500/40 text-teal-300 font-bold';
    return 'bg-indigo-500/15 border-indigo-500/30 text-indigo-300 font-semibold';
  };

  return (
    <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight">Posture Transition Heatmap</h3>
          <p className="text-xs text-slate-400 mt-0.5">Visual matrix of posture changes (From Row → To Column)</p>
        </div>
        <div className="flex items-center space-x-2 text-[10px] text-slate-400">
          <span>Low</span>
          <div className="w-12 h-2 rounded bg-gradient-to-r from-indigo-900 via-teal-700 to-cyan-400" />
          <span>High</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-center text-xs">
          <thead>
            <tr>
              <th className="p-2 text-slate-500 font-mono text-[10px] uppercase">FROM \ TO</th>
              {POSTURES.map((p) => (
                <th key={p} className="p-2.5 font-mono font-bold text-slate-300 bg-slate-950/60 rounded-t-lg">
                  {p}
                  <div className="text-[10px] text-slate-500 font-sans font-normal truncate">{getPostureLabel(p)}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {POSTURES.map((fromP) => (
              <tr key={fromP}>
                <td className="p-2.5 font-mono font-bold text-slate-300 bg-slate-950/60 text-left rounded-l-lg">
                  {fromP}
                  <div className="text-[10px] text-slate-500 font-sans font-normal truncate">{getPostureLabel(fromP)}</div>
                </td>
                {POSTURES.map((toP) => {
                  if (fromP === toP) {
                    return (
                      <td key={toP} className="p-2.5 bg-slate-950/40 text-slate-700 font-mono text-xs">
                        —
                      </td>
                    );
                  }
                  const key = `${fromP}->${toP}`;
                  const count = transitions[key] || 0;
                  const colorClass = getHeatmapColor(count);
                  return (
                    <td key={toP} className="p-1">
                      <div className={`p-3 rounded-xl border transition-all ${colorClass}`}>
                        <div className="text-sm font-mono">{count}</div>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
