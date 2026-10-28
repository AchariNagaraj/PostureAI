// src/components/RecommendationCard.jsx
import React from 'react';
import { ShieldIcon } from './Icons';

export default function RecommendationCard({ recommendation }) {
  if (!recommendation) {
    return (
      <div className="p-4 bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800/80 text-xs text-slate-400 flex items-center space-x-2">
        <ShieldIcon className="w-4 h-4 text-slate-500" />
        <span>No active recommendation. Maintaining regular observation.</span>
      </div>
    );
  }
  const title = typeof recommendation === 'string' ? 'Postural Alignment Guidance' : (recommendation.title || 'Observation Note');
  const description = typeof recommendation === 'string' ? recommendation : (recommendation.description || '');

  return (
    <div className="p-5 bg-gradient-to-r from-indigo-950/40 to-slate-900/90 backdrop-blur-md rounded-2xl border border-indigo-500/20 shadow-xl space-y-1.5">
      <div className="flex items-center space-x-2 text-indigo-400 font-semibold text-sm">
        <ShieldIcon className="w-4 h-4" />
        <h4>{title}</h4>
      </div>
      <p className="text-xs text-slate-300 leading-relaxed">{description}</p>
    </div>
  );
}
