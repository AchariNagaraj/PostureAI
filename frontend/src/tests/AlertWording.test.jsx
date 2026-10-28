// src/tests/AlertWording.test.jsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import AlertBanner from '../components/AlertBanner';
import RecommendationCard from '../components/RecommendationCard';

describe('Posture Alert Wording Tests', () => {
  it('renders exact updated posture alert wording in AlertBanner', () => {
    const alertEvent = {
      timestamp: 100,
      posture: 'TLF',
      alert_type: 'PERSISTENT_TLF',
      risk_score: 0.85,
      risk_level: 'BAD',
      message: "You're compromising with your posture. Please correct your posture.",
      voice_message: "You're compromising with your posture. Please correct your posture.",
    };

    render(<AlertBanner alertEvent={alertEvent} dismiss={() => {}} />);
    expect(screen.getByText("You're compromising with your posture. Please correct your posture.")).toBeInTheDocument();
    expect(screen.getByText('PERSISTENT_TLF')).toBeInTheDocument();
  });

  it('renders exact updated recommendation wording in RecommendationCard', () => {
    const recommendation = {
      title: 'Postural Alignment Guidance',
      description: "You're compromising with your posture. Please correct your posture.",
    };

    render(<RecommendationCard recommendation={recommendation} />);
    expect(screen.getByText("You're compromising with your posture. Please correct your posture.")).toBeInTheDocument();
  });
});
