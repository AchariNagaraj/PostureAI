// src/tests/AnalyticsPages.test.jsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import KpiCard from '../components/KpiCard';
import PostureDistributionChart from '../components/PostureDistributionChart';
import SessionTimelineChart from '../components/SessionTimelineChart';

describe('Analytics & Reports Components', () => {
  it('renders KpiCard with title and value', () => {
    render(<KpiCard title="Total Duration" value="120.0s" subtext="Observed time" icon="⏱️" />);
    expect(screen.getByText('Total Duration')).toBeInTheDocument();
    expect(screen.getByText('120.0s')).toBeInTheDocument();
    expect(screen.getByText('Observed time')).toBeInTheDocument();
  });

  it('renders PostureDistributionChart empty state gracefully', () => {
    render(<PostureDistributionChart posturesData={{}} />);
    expect(screen.getByText(/No posture metrics recorded/i)).toBeInTheDocument();
  });

  it('renders SessionTimelineChart empty state gracefully', () => {
    render(<SessionTimelineChart timeline={[]} alerts={[]} />);
    expect(screen.getByText(/No timeline metrics available/i)).toBeInTheDocument();
  });
});
