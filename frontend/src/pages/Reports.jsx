// src/pages/Reports.jsx
import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import SessionTimelineChart from '../components/SessionTimelineChart';
import ErrorState from '../components/ErrorState';
import { Skeleton } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import { getPostureLabel } from '../utils/postureLabels';
import { ReportsIcon } from '../components/Icons';

export default function Reports() {
  const [searchParams] = useSearchParams();
  const initialSessionQuery = searchParams.get('session');

  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [report, setReport] = useState(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState(null);

  // Fetch session list for selector
  useEffect(() => {
    async function fetchSessions() {
      try {
        setLoadingSessions(true);
        setError(null);
        const res = await fetch('/api/analytics/sessions?limit=50');
        if (!res.ok) throw new Error('Failed to fetch session list');
        const data = await res.json();
        const list = data.sessions || [];
        setSessions(list);
        if (list.length > 0) {
          if (initialSessionQuery && list.some((s) => s.id === Number(initialSessionQuery))) {
            setSelectedSessionId(Number(initialSessionQuery));
          } else {
            setSelectedSessionId(list[0].id);
          }
        }
      } catch (err) {
        setError(err.message || 'Error loading sessions');
      } finally {
        setLoadingSessions(false);
      }
    }
    fetchSessions();
  }, [initialSessionQuery]);

  // Fetch report details when selectedSessionId changes
  useEffect(() => {
    if (!selectedSessionId) return;
    async function fetchReport() {
      try {
        setLoadingReport(true);
        setError(null);
        const res = await fetch(`/api/reports/sessions/${selectedSessionId}`);
        if (!res.ok) throw new Error(`Failed to load report for session #${selectedSessionId}`);
        const data = await res.json();
        setReport(data);
      } catch (err) {
        setError(err.message || 'Error loading report');
      } finally {
        setLoadingReport(false);
      }
    }
    fetchReport();
  }, [selectedSessionId]);

  if (loadingSessions) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <ReportsIcon className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Session Inspection Reports</h1>
            <p className="text-xs text-slate-400">Detailed session-by-session sitting posture timelines.</p>
          </div>
        </div>
        <div className="text-sm text-slate-400">Loading sessions...</div>
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
            <ReportsIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Session Inspection Reports</h1>
            <p className="text-xs text-slate-400 mt-0.5">Comprehensive timeline & risk breakdown per session</p>
          </div>
        </div>

        {/* Session Selector */}
        {sessions.length > 0 && (
          <div className="flex items-center space-x-2">
            <label htmlFor="session-select" className="text-xs font-semibold text-slate-300">
              Select Session:
            </label>
            <select
              id="session-select"
              value={selectedSessionId || ''}
              onChange={(e) => setSelectedSessionId(Number(e.target.value))}
              className="bg-slate-950 border border-slate-700 text-white text-xs font-medium rounded-xl px-3 py-2 focus:outline-none focus:border-cyan-500 shadow-sm"
            >
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  Session #{s.id} — {s.created_at || 'UTC'} ({s.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {error && <ErrorState message={error} onRetry={() => setSelectedSessionId(selectedSessionId)} />}

      {sessions.length === 0 ? (
        <EmptyState
          title="No completed sessions available"
          description="Select a completed session to view its report. Session history will appear once a monitoring session is completed."
        />
      ) : loadingReport ? (
        <div className="space-y-4">
          <div className="text-sm text-slate-400">Loading session report...</div>
          <Skeleton className="h-44 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
      ) : report ? (
        <div className="space-y-6">
          {/* Executive Summary Banner */}
          <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <div className="flex flex-wrap justify-between items-center gap-2">
              <div>
                <h2 className="text-lg font-bold text-white tracking-tight">
                  Session #{report.session_id} Summary
                </h2>
                <span className="text-xs text-slate-400">Created: {report.created_at || '—'}</span>
              </div>
              <span
                className={`px-3 py-1 text-xs rounded-full font-semibold border ${
                  report.status === 'COMPLETED'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}
              >
                {report.status}
              </span>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-center">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
                <div className="text-[11px] text-slate-400 uppercase font-medium">Observed Duration</div>
                <div className="text-lg font-bold text-cyan-400 font-mono mt-0.5">
                  {report.observed_duration_seconds.toFixed(1)}s
                </div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
                <div className="text-[11px] text-slate-400 uppercase font-medium">Upright Ratio</div>
                <div className="text-lg font-bold text-emerald-400 font-mono mt-0.5">
                  {((report.upright_duration_ratio || 0) * 100).toFixed(1)}%
                </div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
                <div className="text-[11px] text-slate-400 uppercase font-medium">Total Alerts</div>
                <div className="text-lg font-bold text-rose-400 font-mono mt-0.5">{report.total_alerts}</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
                <div className="text-[11px] text-slate-400 uppercase font-medium">Valid Transitions</div>
                <div className="text-lg font-bold text-indigo-400 font-mono mt-0.5">
                  {report.total_transitions}
                </div>
              </div>
            </div>

            {/* Engineering Summary Text */}
            {report.engineering_summary && (
              <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs text-slate-300 space-y-1">
                <span className="font-semibold text-slate-200">Deterministic Summary:</span>
                <p className="leading-relaxed">{report.engineering_summary}</p>
              </div>
            )}
          </div>

          {/* Timeline Chart */}
          <SessionTimelineChart
            timeline={report.timeline || []}
            alerts={report.alerts || []}
          />

          {/* Chronological Alert Log */}
          <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-white tracking-tight">Chronological Alert Log</h3>
            {report.alerts.length === 0 ? (
              <div className="text-slate-400 text-sm py-4 text-center">
                No alert events recorded during this session.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/80 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="p-3">Alert ID</th>
                      <th className="p-3">Timestamp</th>
                      <th className="p-3">Posture</th>
                      <th className="p-3">Alert Type</th>
                      <th className="p-3">Message</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {report.alerts.map((a) => (
                      <tr key={a.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3 font-mono text-slate-400">#{a.id}</td>
                        <td className="p-3 font-mono text-cyan-400">{a.timestamp.toFixed(2)}s</td>
                        <td className="p-3 font-semibold text-rose-400">{getPostureLabel(a.posture)}</td>
                        <td className="p-3 text-xs">
                          <span className="px-2 py-0.5 bg-rose-500/10 text-rose-300 border border-rose-500/30 rounded-full font-mono">
                            {a.alert_type}
                          </span>
                        </td>
                        <td className="p-3 text-slate-200">{a.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
