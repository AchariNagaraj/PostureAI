// src/components/EmptyState.jsx
import React from 'react';
import { AnalyticsIcon } from './Icons';

export default function EmptyState({
  title = 'No data available',
  description = 'Your monitoring metrics and history will appear here once data is recorded.',
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-slate-900/40 border border-slate-800/80 rounded-xl space-y-3">
      <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700/50 flex items-center justify-center text-slate-400">
        <AnalyticsIcon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-slate-200">{title}</h3>
      <p className="text-sm text-slate-400 max-w-sm">{description}</p>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
}
