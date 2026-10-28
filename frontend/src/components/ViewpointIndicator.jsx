// src/components/ViewpointIndicator.jsx
import React from 'react';
import { getViewpointLabel } from '../utils/postureLabels';

export default function ViewpointIndicator({ viewpoint }) {
  const display = getViewpointLabel(viewpoint);

  return (
    <div className="p-4 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-2">
      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        Camera Viewpoint
      </div>
      <div className="flex items-center space-x-2">
        <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
          {display}
        </span>
      </div>
    </div>
  );
}
