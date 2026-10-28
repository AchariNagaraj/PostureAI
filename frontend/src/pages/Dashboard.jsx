// src/pages/Dashboard.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import KpiCard from '../components/KpiCard';
import PostureDistributionChart from '../components/PostureDistributionChart';
import TransitionHeatmap from '../components/TransitionHeatmap';
import { DashboardSkeleton } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import { getPostureLabel, getPostureFullLabel } from '../utils/postureLabels';
import { DashboardIcon, ReportsIcon } from '../components/Icons';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [posturesData, setPosturesData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeBreakdownTab, setActiveBreakdownTab] = useState('ALL');
  const [showBreakdownTable, setShowBreakdownTable] = useState(true);
  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumRes, posRes, sessRes] = await Promise.all([
        fetch('/api/analytics/summary'),
        fetch('/api/analytics/postures'),
        fetch('/api/analytics/sessions?limit=5'),
      ]);

      if (!sumRes.ok || !posRes.ok || !sessRes.ok) {
        throw new Error('Failed to load dashboard analytics');
      }

      const sumData = await sumRes.json();
      const posData = await posRes.json();
      const sessData = await sessRes.json();

      setSummary(sumData);
      setPosturesData(posData);
      setSessions(sessData.sessions || []);
    } catch (err) {
      setError(err.message || 'Error fetching dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatDuration = (seconds) => {
    if (!seconds || seconds <= 0) return '0s';
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <DashboardIcon className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Posture Dashboard</h1>
            <p className="text-xs text-slate-400">Overview of your posture monitoring history and analytics.</p>
          </div>
        </div>
        <div className="text-sm text-slate-400">Loading dashboard...</div>
        <DashboardSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <DashboardIcon className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Posture Dashboard</h1>
            <p className="text-xs text-slate-400">Overview of your posture monitoring history and analytics.</p>
          </div>
        </div>
        <ErrorState message={error} onRetry={fetchData} />
      </div>
    );
  }

  const hasNoData = !summary || (summary.total_sessions === 0 && sessions.length === 0);
  const postures = posturesData?.postures || {};
  const transitions = posturesData?.transitions || {};
  const totalObs = posturesData?.total_observation_count || 0;
  const headAlign = posturesData?.head_alignment;
  const shoulderAlign = posturesData?.shoulder_alignment;

  const trunkRows = Object.entries(postures).map(([key, item]) => ({
    id: `trunk-${key}`,
    category: 'Trunk',
    categoryBadge: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
    code: key,
    label: getPostureFullLabel(key),
    obsCount: item.observation_count,
    countPct: `${item.percentage_by_count}%`,
    durationFormatted: formatDuration(item.duration_seconds),
    durationPct: `${item.percentage_by_duration}%`,
  }));

  const headRows = headAlign
    ? [
        {
          id: 'head-straight',
          category: 'Head',
          categoryBadge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
          code: 'HEAD_STRAIGHT',
          label: 'Head Straight (Pitch & Roll Aligned)',
          obsCount: totalObs > 0 ? Math.round(totalObs * (headAlign.straight_percentage / 100)) : '—',
          countPct: `${headAlign.straight_percentage}%`,
          durationFormatted: formatDuration(headAlign.straight_duration_seconds),
          durationPct: `${headAlign.straight_percentage}%`,
        },
        {
          id: 'head-tilt',
          category: 'Head',
          categoryBadge: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
          code: 'HEAD_TILT',
          label: 'Head Tilt / Forward Head Displacement',
          obsCount: totalObs > 0 ? Math.round(totalObs * (headAlign.tilt_percentage / 100)) : '—',
          countPct: `${headAlign.tilt_percentage}%`,
          durationFormatted: formatDuration(headAlign.tilt_duration_seconds),
          durationPct: `${headAlign.tilt_percentage}%`,
        },
      ]
    : [];

  const shoulderRows = shoulderAlign
    ? [
        {
          id: 'shoulder-aligned',
          category: 'Shoulder',
          categoryBadge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
          code: 'SHOULDERS_ALIGNED',
          label: 'Shoulders Level & Aligned',
          obsCount: totalObs > 0 ? Math.round(totalObs * (shoulderAlign.aligned_percentage / 100)) : '—',
          countPct: `${shoulderAlign.aligned_percentage}%`,
          durationFormatted: formatDuration(shoulderAlign.aligned_duration_seconds),
          durationPct: `${shoulderAlign.aligned_percentage}%`,
        },
        {
          id: 'shoulder-misaligned',
          category: 'Shoulder',
          categoryBadge: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
          code: 'SHOULDER_MISALIGNED',
          label: 'Shoulder Height Asymmetry / Imbalance',
          obsCount: totalObs > 0 ? Math.round(totalObs * (shoulderAlign.misaligned_percentage / 100)) : '—',
          countPct: `${shoulderAlign.misaligned_percentage}%`,
          durationFormatted: formatDuration(shoulderAlign.misaligned_duration_seconds),
          durationPct: `${shoulderAlign.misaligned_percentage}%`,
        },
      ]
    : [];

  const allBreakdownRows = [...trunkRows, ...headRows, ...shoulderRows];

  const visibleRows =
    activeBreakdownTab === 'TRUNK'
      ? trunkRows
      : activeBreakdownTab === 'HEAD'
      ? headRows
      : activeBreakdownTab === 'SHOULDER'
      ? shoulderRows
      : allBreakdownRows;

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
            <DashboardIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Posture Dashboard</h1>
            <p className="text-xs text-slate-400 mt-0.5">Comprehensive overview of your monitoring sessions & posture analytics.</p>
          </div>
        </div>
      </div>

      {hasNoData ? (
        <EmptyState
          title="No monitoring history found"
          description="Your monitoring history will appear here after your first session."
          action={
            <button
              onClick={() => navigate('/live')}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-cyan-600/20 transition"
            >
              Start Monitoring Session
            </button>
          }
        />
      ) : (
        <>
          {/* KPI Summary Grid (4 Operational Metrics, Upright Ratio Removed) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              title="Total Sessions"
              value={summary?.total_sessions}
              subtext={`${summary?.completed_sessions || 0} completed`}
              icon="📊"
            />
            <KpiCard
              title="Observed Duration"
              value={formatDuration(summary?.total_observed_duration_seconds)}
              subtext="Total active monitoring time"
              icon="⏱️"
            />
            <KpiCard
              title="Total Alerts"
              value={summary?.total_alerts}
              subtext={
                summary?.alert_frequency_per_monitoring_hour != null
                  ? `${summary.alert_frequency_per_monitoring_hour}/hr`
                  : 'No alerts'
              }
              icon="⚠️"
            />
            <KpiCard
              title="Avg Session Duration"
              value={formatDuration(summary?.average_session_duration_seconds)}
              subtext="Mean completed session"
              icon="📈"
            />
          </div>

          {/* Charts & Highlights */}
          <div>
            <PostureDistributionChart
              posturesData={postures}
              headAlignment={posturesData?.head_alignment}
              shoulderAlignment={posturesData?.shoulder_alignment}
            />
          </div>

          {/* Posture & Alignment Breakdown Statistics Table (Trunk, Head & Shoulder) */}
          {showBreakdownTable && visibleRows.length > 0 && (
            <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-base font-bold text-white tracking-tight">Posture & Alignment Breakdown</h3>
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 font-medium">
                      Trunk + Head + Shoulder
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">Historical observations across trunk posture, head alignment, and shoulder symmetry.</p>
                </div>

                <div className="flex items-center space-x-2">
                  {/* Category Filter Tabs */}
                  <div className="flex items-center space-x-1 p-1 bg-slate-950/80 rounded-xl border border-slate-800 text-xs">
                    <button
                      onClick={() => setActiveBreakdownTab('ALL')}
                      className={`px-2.5 py-1 rounded-lg font-medium transition ${
                        activeBreakdownTab === 'ALL'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      All ({allBreakdownRows.length})
                    </button>
                    <button
                      onClick={() => setActiveBreakdownTab('TRUNK')}
                      className={`px-2.5 py-1 rounded-lg font-medium transition ${
                        activeBreakdownTab === 'TRUNK'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Trunk ({trunkRows.length})
                    </button>
                    <button
                      onClick={() => setActiveBreakdownTab('HEAD')}
                      className={`px-2.5 py-1 rounded-lg font-medium transition ${
                        activeBreakdownTab === 'HEAD'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Head ({headRows.length})
                    </button>
                    <button
                      onClick={() => setActiveBreakdownTab('SHOULDER')}
                      className={`px-2.5 py-1 rounded-lg font-medium transition ${
                        activeBreakdownTab === 'SHOULDER'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Shoulder ({shoulderRows.length})
                    </button>
                  </div>

                  <button
                    onClick={() => setShowBreakdownTable(false)}
                    title="Remove this table from dashboard view"
                    className="px-2.5 py-1 text-xs text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-500/30 rounded-xl transition"
                  >
                    ✕ Hide
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/80 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="p-3">Category</th>
                      <th className="p-3">Feature / Code</th>
                      <th className="p-3">Human Label</th>
                      <th className="p-3">Observations</th>
                      <th className="p-3">Count %</th>
                      <th className="p-3">Duration</th>
                      <th className="p-3">Duration %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {visibleRows.map((row) => (
                      <tr key={row.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${row.categoryBadge}`}>
                            {row.category}
                          </span>
                        </td>
                        <td className="p-3 font-mono font-bold text-cyan-400">{row.code}</td>
                        <td className="p-3 font-semibold text-white">{row.label}</td>
                        <td className="p-3 text-slate-200">{row.obsCount}</td>
                        <td className="p-3 text-slate-300">{row.countPct}</td>
                        <td className="p-3 text-slate-200 font-mono">{row.durationFormatted}</td>
                        <td className="p-3 font-semibold text-emerald-400">{row.durationPct}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Posture Transition Heatmap */}
          <TransitionHeatmap transitions={transitions} />

          {/* Recent Sessions Table */}
          <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white tracking-tight">Recent Monitoring Sessions</h3>
              <span className="text-xs text-slate-400">Click row to open session report</span>
            </div>

            {sessions.length === 0 ? (
              <div className="text-slate-400 text-sm py-4 text-center">No sessions recorded yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/80 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="p-3">Session ID</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Created</th>
                      <th className="p-3">Duration</th>
                      <th className="p-3">Alerts</th>
                      <th className="p-3 text-right">Report</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {sessions.map((s) => (
                      <tr
                        key={s.id}
                        onClick={() => navigate(`/reports?session=${s.id}`)}
                        className="hover:bg-slate-800/50 transition cursor-pointer group"
                      >
                        <td className="p-3 font-mono font-semibold text-cyan-400">#{s.id}</td>
                        <td className="p-3">
                          <span
                            className={`px-2.5 py-0.5 text-xs rounded-full font-semibold border ${
                              s.status === 'COMPLETED'
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                            }`}
                          >
                            {s.status}
                          </span>
                        </td>
                        <td className="p-3 text-slate-300">{s.created_at || '—'}</td>
                        <td className="p-3 text-slate-200">{formatDuration(s.observed_duration_seconds)}</td>
                        <td className="p-3 text-rose-400 font-semibold">{s.total_alerts}</td>
                        <td className="p-3 text-right">
                          <span className="inline-flex items-center space-x-1 text-xs text-slate-400 group-hover:text-cyan-400 transition">
                            <span>View</span>
                            <ReportsIcon className="w-4 h-4" />
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
