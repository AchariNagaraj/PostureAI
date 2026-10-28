// src/components/SessionTimelineChart.jsx
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts';
import { getPostureLabel } from '../utils/postureLabels';

export default function SessionTimelineChart({ timeline, alerts = [] }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="p-6 bg-slate-900/90 text-slate-400 rounded-2xl border border-slate-800 text-center text-sm shadow-xl">
        No timeline metrics available for this session.
      </div>
    );
  }

  const firstTs = timeline[0].timestamp;
  const chartData = timeline.map((pt) => ({
    relativeTime: Math.max(0, Math.round(pt.timestamp - firstTs)),
    timestamp: pt.timestamp,
    risk_score: pt.risk_score,
    posture: pt.posture,
    humanPosture: getPostureLabel(pt.posture),
    temporal_state: pt.temporal_state,
    is_alert: pt.is_alert_event,
  }));

  const alertDots = chartData.filter((d) => d.is_alert);

  return (
    <div className="p-6 bg-slate-900/90 text-white rounded-2xl border border-slate-800 shadow-xl space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-100 tracking-tight">Risk Score & Alert Timeline</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Temporal risk score trajectory over session elapsed time (seconds).
          </p>
        </div>
      </div>
      <div className="h-64 pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <XAxis
              dataKey="relativeTime"
              unit="s"
              stroke="#64748B"
              tick={{ fill: '#94A3B8', fontSize: 11 }}
              label={{ value: 'Elapsed Time (seconds)', position: 'insideBottom', offset: -10, fill: '#64748B', fontSize: 11 }}
            />
            <YAxis
              domain={[0, 1]}
              ticks={[0, 0.25, 0.5, 0.75, 1.0]}
              stroke="#64748B"
              tick={{ fill: '#94A3B8', fontSize: 11 }}
              label={{ value: 'Risk Score', angle: -90, position: 'insideLeft', fill: '#64748B', fontSize: 11 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 shadow-xl space-y-1">
                      <p><strong className="text-slate-400">Elapsed:</strong> {data.relativeTime}s</p>
                      <p><strong className="text-slate-400">Posture:</strong> {data.humanPosture} ({data.posture})</p>
                      <p><strong className="text-slate-400">Risk Score:</strong> <span className="font-mono font-bold text-rose-400">{data.risk_score.toFixed(2)}</span></p>
                      <p><strong className="text-slate-400">Temporal State:</strong> {data.temporal_state}</p>
                      {data.is_alert && <p className="text-rose-400 font-bold flex items-center space-x-1 pt-1"><span>⚠️ Alert Event</span></p>}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Line
              type="stepAfter"
              dataKey="risk_score"
              stroke="#F43F5E"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#F43F5E' }}
            />
            {alertDots.map((dot, idx) => (
              <ReferenceDot
                key={idx}
                x={dot.relativeTime}
                y={dot.risk_score}
                r={6}
                fill="#E11D48"
                stroke="#FFFFFF"
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
