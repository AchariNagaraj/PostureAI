// src/pages/Analytics.jsx
import React, { useEffect, useState } from 'react';
import PostureDistributionChart from '../components/PostureDistributionChart';
import TransitionHeatmap from '../components/TransitionHeatmap';
import KpiCard from '../components/KpiCard';
import ErrorState from '../components/ErrorState';
import { Skeleton } from '../components/Skeleton';
import { getPostureLabel, getPostureFullLabel } from '../utils/postureLabels';
import { AnalyticsIcon } from '../components/Icons';

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/analytics/postures');
      if (!res.ok) throw new Error('Failed to fetch posture analytics');
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err.message || 'Error loading analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <AnalyticsIcon className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Posture & Risk Analytics</h1>
            <p className="text-xs text-slate-400">Detailed historical posture observations & state transitions.</p>
          </div>
        </div>
        <div className="text-sm text-slate-400">Loading detailed posture analytics...</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <AnalyticsIcon className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Posture & Risk Analytics</h1>
            <p className="text-xs text-slate-400">Detailed historical posture observations & state transitions.</p>
          </div>
        </div>
        <ErrorState message={error} onRetry={fetchAnalytics} />
      </div>
    );
  }

  const postures = data?.postures || {};
  const transitions = data?.transitions || {};

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
            <AnalyticsIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Posture & Risk Analytics</h1>
            <p className="text-xs text-slate-400 mt-0.5">Comprehensive historical observations & posture transition metrics</p>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          title="Total Observations"
          value={data?.total_observation_count}
          subtext="Total frame metrics"
          icon="📷"
        />
        <KpiCard
          title="Observed Duration"
          value={`${(data?.total_observed_duration_seconds || 0).toFixed(1)}s`}
          subtext="Valid metric intervals"
          icon="⏱️"
        />
        <KpiCard
          title="Upright Duration Ratio"
          value={`${((data?.upright_duration_ratio || 0) * 100).toFixed(1)}%`}
          subtext="TUP duration / total duration"
          icon="🎯"
        />
      </div>

      {/* Distribution Chart Section */}
      <PostureDistributionChart posturesData={postures} />

      {/* Posture Metrics Breakdown Table */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white tracking-tight">Posture Observation & Duration Statistics</h3>
          <span className="text-xs text-slate-400">Class breakdown</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-3">Posture Class</th>
                <th className="p-3">Human Readable Label</th>
                <th className="p-3">Observation Count</th>
                <th className="p-3">Count %</th>
                <th className="p-3">Observed Duration</th>
                <th className="p-3">Duration %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {Object.entries(postures).map(([key, item]) => (
                <tr key={key} className="hover:bg-slate-800/40 transition">
                  <td className="p-3 font-mono font-bold text-cyan-400">{key}</td>
                  <td className="p-3 font-semibold text-white">{getPostureFullLabel(key)}</td>
                  <td className="p-3 text-slate-200">{item.observation_count}</td>
                  <td className="p-3 text-slate-300">{item.percentage_by_count}%</td>
                  <td className="p-3 text-slate-200 font-mono">{item.duration_seconds.toFixed(1)}s</td>
                  <td className="p-3 font-semibold text-emerald-400">{item.percentage_by_duration}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Posture Transition Heatmap */}
      <TransitionHeatmap transitions={transitions} />

      {/* Posture Alignment Metrics (Head, Trunk & Shoulder) */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight">Postural Feature Monitoring (Head, Trunk & Shoulder)</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time ergonomic parameters evaluated across posture predictions.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">Head Posture</span>
              <span className="text-[10px] px-2 py-0.5 bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 rounded-full font-mono">Monitored</span>
            </div>
            <p className="text-sm font-semibold text-white">Head Pitch, Roll & Forward Displacement</p>
            <p className="text-xs text-emerald-400 font-medium font-mono">Target: keep your head straight</p>
          </div>

          <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Trunk Posture</span>
              <span className="text-[10px] px-2 py-0.5 bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 rounded-full font-mono">Monitored</span>
            </div>
            <p className="text-sm font-semibold text-white">Torso Pitch, Lateral Tilt & Rotation</p>
            <p className="text-xs text-emerald-400 font-medium font-mono">Target: trunk straight</p>
          </div>

          <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Shoulder Posture</span>
              <span className="text-[10px] px-2 py-0.5 bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 rounded-full font-mono">Monitored</span>
            </div>
            <p className="text-sm font-semibold text-white">Left/Right Shoulder Height Asymmetry</p>
            <p className="text-xs text-emerald-400 font-medium font-mono">Target: shoulder aligned</p>
          </div>
        </div>
      </div>
    </div>
  );
}
