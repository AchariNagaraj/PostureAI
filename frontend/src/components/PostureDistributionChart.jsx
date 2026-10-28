// src/components/PostureDistributionChart.jsx
import React, { useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { POSTURE_CLASS_MAP } from '../utils/postureLabels';

const TRUNK_COLORS = {
  TUP: '#10B981', // green
  TLF: '#EF4444', // red
  TLB: '#F59E0B', // amber
  TLL: '#3B82F6', // blue
  TLR: '#8B5CF6', // purple
};

const HEAD_COLORS = {
  HEAD_STRAIGHT: '#10B981', // green
  HEAD_TILT: '#F43F5E',    // rose red
};

const SHOULDER_COLORS = {
  SHOULDERS_ALIGNED: '#10B981',    // green
  SHOULDER_MISALIGNED: '#F97316', // orange
};

export default function PostureDistributionChart({ posturesData, headAlignment, shoulderAlignment }) {
  const [activeTab, setActiveTab] = useState('TRUNK'); // 'TRUNK' | 'HEAD' | 'SHOULDER'

  if (!posturesData || Object.keys(posturesData).length === 0) {
    return (
      <div className="p-6 bg-slate-900/90 text-slate-400 rounded-2xl border border-slate-800 text-center text-sm shadow-xl">
        No posture metrics recorded.
      </div>
    );
  }

  // 1. Trunk chart data
  const trunkData = Object.entries(posturesData).map(([key, item]) => ({
    name: POSTURE_CLASS_MAP[key] ? `${POSTURE_CLASS_MAP[key]} (${key})` : key,
    key,
    duration: item.duration_seconds || 0,
    percentage: item.percentage_by_duration || 0,
    count: item.observation_count || 0,
  }));

  // 2. Head alignment chart data
  const headData = headAlignment ? [
    {
      name: 'Head Straight',
      key: 'HEAD_STRAIGHT',
      duration: headAlignment.straight_duration_seconds || 0,
      percentage: headAlignment.straight_percentage || 0,
    },
    {
      name: 'Head Tilt / Forward',
      key: 'HEAD_TILT',
      duration: headAlignment.tilt_duration_seconds || 0,
      percentage: headAlignment.tilt_percentage || 0,
    }
  ] : [];

  // 3. Shoulder alignment chart data
  const shoulderData = shoulderAlignment ? [
    {
      name: 'Shoulders Aligned',
      key: 'SHOULDERS_ALIGNED',
      duration: shoulderAlignment.aligned_duration_seconds || 0,
      percentage: shoulderAlignment.aligned_percentage || 0,
    },
    {
      name: 'Shoulder Misalignment',
      key: 'SHOULDER_MISALIGNED',
      duration: shoulderAlignment.misaligned_duration_seconds || 0,
      percentage: shoulderAlignment.misaligned_percentage || 0,
    }
  ] : [];

  let currentData = trunkData;
  let currentColors = TRUNK_COLORS;
  let chartTitle = 'Trunk Posture Distribution';

  if (activeTab === 'HEAD') {
    currentData = headData;
    currentColors = HEAD_COLORS;
    chartTitle = 'Head Posture Alignment';
  } else if (activeTab === 'SHOULDER') {
    currentData = shoulderData;
    currentColors = SHOULDER_COLORS;
    chartTitle = 'Shoulder Posture Alignment';
  }

  const hasData = currentData.some((d) => d.duration > 0 || (d.percentage && d.percentage > 0));

  return (
    <div className="p-6 bg-slate-900/90 text-white rounded-2xl border border-slate-800 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h3 className="text-base font-bold text-slate-100 tracking-tight">{chartTitle}</h3>
        
        {/* Metric Selector Tabs */}
        <div className="flex items-center space-x-1 p-1 bg-slate-950/80 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('TRUNK')}
            className={`px-2.5 py-1 rounded-lg font-medium transition ${
              activeTab === 'TRUNK' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Trunk
          </button>
          <button
            onClick={() => setActiveTab('HEAD')}
            className={`px-2.5 py-1 rounded-lg font-medium transition ${
              activeTab === 'HEAD' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Head Posture
          </button>
          <button
            onClick={() => setActiveTab('SHOULDER')}
            className={`px-2.5 py-1 rounded-lg font-medium transition ${
              activeTab === 'SHOULDER' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Shoulder Alignment
          </button>
        </div>
      </div>

      {!hasData ? (
        <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
          No metrics recorded for selected view.
        </div>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={currentData}
                dataKey="duration"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={85}
                innerRadius={50}
                paddingAngle={3}
                label={({ key, percentage }) => `${percentage}%`}
              >
                {currentData.map((entry) => (
                  <Cell key={entry.key} fill={currentColors[entry.key] || '#64748B'} stroke="#0f172a" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name, item) => [
                  `${value.toFixed(1)}s (${item.payload.percentage}%)`,
                  item.payload.name,
                ]}
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '0.75rem', color: '#F8FAFC' }}
              />
              <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
