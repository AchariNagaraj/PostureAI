// src/pages/LiveMonitor.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useMonitoring, MonitoringState } from '../hooks/useMonitoring';
import useAlertManager from '../hooks/useAlertManager';
import { useUI } from '../state/store';
import CameraView from '../components/CameraView';
import PoseOverlay from '../components/PoseOverlay';
import TargetSelector from '../components/TargetSelector';
import ViewpointIndicator from '../components/ViewpointIndicator';
import PostureStatus from '../components/PostureStatus';
import RiskIndicator from '../components/RiskIndicator';
import AlertBanner from '../components/AlertBanner';
import RecommendationCard from '../components/RecommendationCard';
import SessionTimer from '../components/SessionTimer';
import ConnectionStatus from '../components/ConnectionStatus';
import CalibrationCard from '../components/CalibrationCard';
import { LiveIcon, AlertIcon } from '../components/Icons';

export default function LiveMonitor() {
  const {
    state,
    error,
    stream,
    camStatus,
    wsStatus,
    lastMessage,
    start,
    stop,
    sendFrame,
    selectTarget,
    changeTarget,
    startCalibration,
    finalizeCalibration,
  } = useMonitoring();

  const { setWsStatus } = useUI();
  const [sessionStart, setSessionStart] = useState(null);
  const [videoAspect, setVideoAspect] = useState(4 / 3);

  // Calibration state: 'IDLE' | 'CALIBRATING' | 'COMPLETE' | 'MONITORING_ACTIVE' | 'FAILED'
  const [calibMode, setCalibMode] = useState('IDLE');
  const [calibSeconds, setCalibSeconds] = useState(10);
  const [calibFailReason, setCalibFailReason] = useState('');
  const calibSentRef = useRef(false);

  // Grace period: show GOOD for 15 seconds after monitoring starts
  const GRACE_PERIOD_MS = 15000;
  const [monitoringStartedAt, setMonitoringStartedAt] = useState(null);
  const [inGracePeriod, setInGracePeriod] = useState(false);

  // Posture smoothing: only flip display status after 3 consecutive seconds
  const SMOOTH_WINDOW_MS = 3000;
  const [smoothedPostureEval, setSmoothedPostureEval] = useState(null);
  const pendingBadRef = useRef({ status: null, since: null });
  const lastGoodEvalRef = useRef(null);

  // Only feed messages to alert manager when NOT calibrating
  const alertMessage = (calibMode === 'MONITORING_ACTIVE') ? lastMessage : null;
  const { currentAlert, dismiss } = useAlertManager(alertMessage);

  // Sync wsStatus to UIContext for AppShell sidebar
  useEffect(() => {
    if (setWsStatus) {
      setWsStatus(wsStatus);
    }
  }, [wsStatus, setWsStatus]);

  const isCamActive = camStatus === 'ACTIVE';
  const isMonitoring = calibMode === 'MONITORING_ACTIVE';

  // Send START_CALIBRATION to backend once WS is connected and we're in CALIBRATING mode
  useEffect(() => {
    if (calibMode === 'CALIBRATING' && wsStatus === 'CONNECTED' && !calibSentRef.current) {
      startCalibration();
      calibSentRef.current = true;
    }
  }, [calibMode, wsStatus, startCalibration]);

  // 10-Second Calibration Timer
  useEffect(() => {
    let timer = null;
    if (calibMode === 'CALIBRATING' && isCamActive) {
      timer = setInterval(() => {
        setCalibSeconds((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            // Send FINALIZE_CALIBRATION to backend
            finalizeCalibration();
            setCalibMode('COMPLETE');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [calibMode, isCamActive, finalizeCalibration]);

  const handleStartCalibration = () => {
    setCalibSeconds(10);
    setCalibFailReason('');
    calibSentRef.current = false;
    setCalibMode('CALIBRATING');
    start();
  };

  const handleBeginMonitoring = () => {
    const now = Date.now();
    setCalibMode('MONITORING_ACTIVE');
    setSessionStart(now);
    setMonitoringStartedAt(now);
    setInGracePeriod(true);
    setSmoothedPostureEval(null);
    pendingBadRef.current = { status: null, since: null };
  };

  const handleStop = () => {
    stop();
    setCalibMode('IDLE');
    setCalibSeconds(10);
    setSessionStart(null);
    setMonitoringStartedAt(null);
    setInGracePeriod(false);
    setSmoothedPostureEval(null);
    pendingBadRef.current = { status: null, since: null };
    calibSentRef.current = false;
  };

  // Listen for CALIBRATION_STATE messages from backend
  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'CALIBRATION_STATE') return;
    const cs = lastMessage.payload?.calibration_state;
    if (cs === 'CALIBRATION_FAILED') {
      setCalibMode('FAILED');
      setCalibFailReason(lastMessage.payload?.message || 'Calibration failed');
    }
  }, [lastMessage]);

  // Grace period timer — expire after 15 seconds
  useEffect(() => {
    if (!inGracePeriod || !monitoringStartedAt) return;
    const remaining = GRACE_PERIOD_MS - (Date.now() - monitoringStartedAt);
    if (remaining <= 0) { setInGracePeriod(false); return; }
    const t = setTimeout(() => setInGracePeriod(false), remaining);
    return () => clearTimeout(t);
  }, [inGracePeriod, monitoringStartedAt]);

  // Posture smoothing — 3-second debounce before flipping to BAD/MODERATE
  useEffect(() => {
    if (!isMonitoring || inGracePeriod) return;
    const rawEval = lastMessage?.payload?.posture_evaluation;
    if (!rawEval) return;
    const rawStatus = rawEval.overall_status;
    if (!rawStatus || rawStatus === 'UNKNOWN') return;

    if (rawStatus === 'GOOD') {
      // Immediately clear any pending bad transition and show GOOD
      pendingBadRef.current = { status: null, since: null };
      lastGoodEvalRef.current = rawEval;
      setSmoothedPostureEval(rawEval);
      return;
    }

    // BAD or MODERATE — only commit after SMOOTH_WINDOW_MS of sustained deviation
    const now = Date.now();
    if (pendingBadRef.current.status !== rawStatus) {
      // Status changed — restart the window
      pendingBadRef.current = { status: rawStatus, since: now };
    } else {
      const elapsed = now - pendingBadRef.current.since;
      if (elapsed >= SMOOTH_WINDOW_MS) {
        setSmoothedPostureEval(rawEval);
      }
      // else: keep showing last good eval until window expires
    }
  }, [lastMessage, isMonitoring, inGracePeriod]);


  // Extract fields from payload for display
  const payload = lastMessage?.payload || {};
  const {
    posture,
    confidence,
    viewpoint,
    person_state,
    tracking_state,
    target_id,
    candidates,
    risk_score,
    risk_level,
    temporal_state,
    pose_valid,
    fps,
  } = payload;

  // Determine what posture evaluation to display:
  // - During grace period: force all GOOD
  // - After grace period: use 3-second smoothed eval
  const GOOD_EVAL = {
    overall_status: 'GOOD',
    head: { status: 'GOOD', detail: 'Head straight' },
    shoulder: { status: 'GOOD', detail: 'Shoulders aligned' },
    trunk: { status: 'GOOD', detail: 'Trunk straight' },
  };
  const displayedPostureEval = !isMonitoring
    ? payload.posture_evaluation
    : inGracePeriod
    ? GOOD_EVAL
    : (smoothedPostureEval || lastGoodEvalRef.current || GOOD_EVAL);

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
            <LiveIcon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-white tracking-tight">Live Posture Monitoring</h1>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border flex items-center space-x-1.5 ${
                isMonitoring
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : calibMode === 'CALIBRATING'
                  ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                  : isCamActive
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  isMonitoring ? 'bg-emerald-500 animate-pulse' : calibMode === 'CALIBRATING' ? 'bg-cyan-500 animate-pulse' : isCamActive ? 'bg-amber-500 animate-pulse' : 'bg-slate-500'
                }`} />
                <span>{isMonitoring ? 'Monitoring' : calibMode === 'CALIBRATING' ? 'Calibrating' : isCamActive ? 'Camera Active' : 'Not Monitoring'}</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Real-time pose estimation and temporal sitting risk assessment</p>
          </div>
        </div>

        {/* Controls & Notification Channel Toggles */}
        <div className="flex flex-wrap items-center gap-3">
          {isCamActive && sessionStart && <SessionTimer startTime={sessionStart} />}

          {/* Quick Notification Controls */}
          <div className="flex items-center space-x-1.5 p-1 bg-slate-950/80 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => {
                const next = !useUI().notificationEnabled;
                if (next && typeof window !== 'undefined' && 'Notification' in window && Notification.permission !== 'granted') {
                  Notification.requestPermission();
                }
                useUI().setNotificationEnabled(next);
                try { localStorage.setItem('notificationEnabled', JSON.stringify(next)); } catch (e) {}
              }}
              title="Toggle System OS Popup Notification"
              className={`px-2 py-1 rounded-lg font-medium transition ${
                useUI().notificationEnabled ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              🔔 System
            </button>
            <button
              onClick={() => {
                const next = !useUI().soundEnabled;
                useUI().setSoundEnabled(next);
                try { localStorage.setItem('soundEnabled', JSON.stringify(next)); } catch (e) {}
              }}
              title="Toggle Audio Beep Sound"
              className={`px-2 py-1 rounded-lg font-medium transition ${
                useUI().soundEnabled ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              🎵 Beep
            </button>
            <button
              onClick={() => {
                const next = !useUI().voiceEnabled;
                useUI().setVoiceEnabled(next);
                try { localStorage.setItem('voiceEnabled', JSON.stringify(next)); } catch (e) {}
              }}
              title="Toggle Voice Speech Synthesis"
              className={`px-2 py-1 rounded-lg font-medium transition ${
                useUI().voiceEnabled ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              🗣️ Voice
            </button>
          </div>

          {isCamActive ? (
            <button
              onClick={handleStop}
              className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-rose-600/25 flex items-center space-x-2"
            >
              <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
              <span>Stop Monitoring</span>
            </button>
          ) : (
            <button
              onClick={handleStartCalibration}
              disabled={state === MonitoringState.STARTING}
              className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-cyan-500/25 flex items-center space-x-2 disabled:opacity-50"
            >
              <LiveIcon className="w-4 h-4" />
              <span>{state === MonitoringState.STARTING ? 'Starting...' : 'Start Monitoring'}</span>
            </button>
          )}
        </div>
      </div>

      {/* 10-Second Calibration Card Banner */}
      {(calibMode === 'CALIBRATING' || calibMode === 'COMPLETE' || calibMode === 'FAILED') && (
        <CalibrationCard
          progress={((10 - calibSeconds) / 10) * 100}
          secondsRemaining={calibSeconds}
          poseValid={pose_valid !== false}
          trackingState={tracking_state || 'ONE_PERSON'}
          viewpoint={viewpoint || 'FRONT'}
          isComplete={calibMode === 'COMPLETE'}
          isFailed={calibMode === 'FAILED'}
          failReason={calibFailReason}
          onStartMonitoring={handleBeginMonitoring}
          onCancel={handleStop}
          onTryAgain={handleStartCalibration}
          calibrationInfo={payload.calibration_info}
        />
      )}


      {/* System Status Badges Bar */}
      <div className="px-2">
        <ConnectionStatus
          camStatus={camStatus}
          wsStatus={wsStatus}
          monitorState={state}
        />
      </div>

      {/* General Error Banner if present */}
      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/60 text-rose-200 rounded-xl text-xs flex items-center space-x-2">
          <AlertIcon className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>Notice: {error}</span>
        </div>
      )}

      {/* Alert Banner if alert event emitted — only when monitoring */}
      {isMonitoring && <AlertBanner alertEvent={currentAlert} dismiss={dismiss} />}

      {/* MAIN CAMERA PANEL AREA */}
      <div className="relative group">
        <CameraView
          stream={stream}
          camStatus={camStatus}
          wsStatus={wsStatus}
          trackingState={tracking_state}
          viewpoint={viewpoint}
          poseValid={pose_valid}
          error={error}
          lastMessage={lastMessage}
          onFrame={sendFrame}
          onStartCam={handleStartCalibration}
          onReconnectWs={handleStartCalibration}
          onAspectChange={setVideoAspect}
        />
        <PoseOverlay
          poseLandmarks={payload.pose_landmarks}
          posture={posture}
          confidence={confidence}
          viewpoint={viewpoint}
          riskScore={risk_score}
          riskLevel={risk_level}
          temporalState={temporal_state}
          trackingState={tracking_state}
          candidates={candidates}
          onSelectCandidate={selectTarget}
          videoAspect={videoAspect}
        />

        {/* Real-time FPS / Viewpoint overlay pill inside camera top-right */}
        {isCamActive && (
          <div className="absolute top-4 right-4 z-20 flex items-center space-x-2">
            {fps != null && (
              <span className="px-2.5 py-1 bg-slate-950/80 border border-slate-800 rounded-lg backdrop-blur-md text-[11px] font-mono text-cyan-400">
                {fps.toFixed(0)} FPS
              </span>
            )}
          </div>
        )}
      </div>

      {/* REAL-TIME METRICS & CARDS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <PostureStatus
          posture={isMonitoring ? posture : undefined}
          confidence={isMonitoring ? confidence : undefined}
          riskLevel={isMonitoring ? risk_level : undefined}
          temporalState={isMonitoring ? temporal_state : undefined}
          postureEvaluation={isMonitoring ? payload.posture_evaluation : undefined}
        />
        <RiskIndicator
          riskScore={isMonitoring ? risk_score : 0}
          riskLevel={isMonitoring ? (temporal_state || risk_level) : 'NORMAL'}
          temporalState={isMonitoring ? temporal_state : 'NORMAL'}
        />
        <ViewpointIndicator viewpoint={viewpoint} />
        <TargetSelector
          personState={person_state}
          trackingState={tracking_state}
          targetId={target_id}
          candidates={candidates}
          onSelectTarget={selectTarget}
          onChangeTarget={changeTarget}
        />
      </div>

      {/* Recommendation Card — only when monitoring */}
      {isMonitoring && <RecommendationCard recommendation={payload.recommendation} />}
    </div>
  );
}
