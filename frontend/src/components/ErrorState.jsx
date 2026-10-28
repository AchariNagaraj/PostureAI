// src/components/ErrorState.jsx
import React from 'react';
import { AlertIcon, RefreshIcon } from './Icons';

export default function ErrorState({
  title = 'Unable to load data',
  message = 'An unexpected error occurred while communicating with PostureAI.',
  onRetry,
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-rose-950/20 border border-rose-800/40 rounded-xl space-y-3">
      <div className="w-12 h-12 rounded-full bg-rose-900/30 border border-rose-700/50 flex items-center justify-center text-rose-400">
        <AlertIcon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-rose-200">{title}</h3>
      <p className="text-sm text-slate-300 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-rose-600/80 hover:bg-rose-600 text-white font-medium text-sm rounded-lg transition border border-rose-500/50 shadow-sm"
        >
          <RefreshIcon className="w-4 h-4" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
