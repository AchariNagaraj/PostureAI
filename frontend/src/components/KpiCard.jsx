// src/components/KpiCard.jsx
import React from 'react';

export default function KpiCard({ title, value, subtext, icon }) {
  return (
    <div className="p-5 bg-gradient-to-b from-slate-800/90 to-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl hover:border-slate-700/80 transition-all group">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-slate-300 transition-colors">
          {title}
        </span>
        {icon && (
          <div className="w-8 h-8 rounded-xl bg-slate-800/80 border border-slate-700/50 flex items-center justify-center text-slate-300 shadow-inner group-hover:scale-105 transition-transform">
            <span className="text-base">{icon}</span>
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-white tracking-tight mb-1">
        {value != null ? value : '—'}
      </div>
      {subtext && (
        <div className="text-xs text-slate-400 flex items-center space-x-1">
          <span>{subtext}</span>
        </div>
      )}
    </div>
  );
}
