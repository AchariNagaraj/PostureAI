// src/hooks/useMonitoring.js
import { useState, useCallback, useEffect, useRef } from 'react';
import { useCamera, CameraStatus } from './useCamera';
import { useWebSocket, WSStatus } from './useWebSocket';

export const MonitoringState = {
  IDLE: 'IDLE',
  STARTING: 'STARTING',
  ACTIVE: 'ACTIVE',
  PAUSED: 'PAUSED',
  STOPPED: 'STOPPED',
  ERROR: 'ERROR',
};

/**
 * Hook managing the end‑to‑end monitoring lifecycle.
 * Guarantees a single START_SESSION per attempt, stores the session ID,
 * and ensures STOP_MONITORING is acknowledged before cleanup.
 */
export function useMonitoring() {
  const [state, setState] = useState(MonitoringState.IDLE);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const startSessionSent = useRef(false); // guard against duplicate START_SESSION
  const stopAckTimer = useRef(null);

  const { stream, status: camStatus, error: camError, start: startCam, stop: stopCam } = useCamera();
  const {
    status: wsStatus,
    error: wsError,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    sendFrame,
    selectTarget,
    changeTarget,
    startCalibration,
    finalizeCalibration,
  } = useWebSocket();

  // ---------- UI actions ----------
  const start = useCallback(() => {
    setState(MonitoringState.STARTING);
    setError(null);
    startCam();
  }, [startCam]);

  const stop = useCallback(() => {
    if (sessionId) {
      sendMessage('STOP_MONITORING', { session_id: sessionId });
      // Wait up to 5 s for SESSION_CLOSED, then force cleanup.
      stopAckTimer.current = setTimeout(() => {
        disconnect();
        setState(MonitoringState.STOPPED);
      }, 5000);
    } else {
      disconnect();
      setState(MonitoringState.STOPPED);
    }
    stopCam();
  }, [sessionId, sendMessage, disconnect, stopCam]);

  // ---------- Camera effect ----------
  useEffect(() => {
    if (camStatus === CameraStatus.ERROR) {
      setError(camError || 'Camera error');
      setState(MonitoringState.ERROR);
      return;
    }
    if (camStatus === CameraStatus.ACTIVE) {
      connect();
    }
    if (camStatus === CameraStatus.STOPPED) {
      disconnect();
    }
  }, [camStatus, camError, connect, disconnect]);

  // ---------- WebSocket connection effect ----------
  useEffect(() => {
    if (wsStatus === WSStatus.CONNECTED && camStatus === CameraStatus.ACTIVE) {
      setState(MonitoringState.ACTIVE);
      if (!startSessionSent.current) {
        const requestId = crypto.randomUUID();
        sendMessage('START_SESSION', { request_id: requestId });
        startSessionSent.current = true;
      }
    }
    if (wsStatus === WSStatus.DISCONNECTED && state === MonitoringState.ACTIVE) {
      setState(MonitoringState.PAUSED);
    }
  }, [wsStatus, camStatus, state, sendMessage]);

  // ---------- Incoming messages ----------
  useEffect(() => {
    if (!lastMessage) return;
    const { type, session_id, message } = lastMessage;
    switch (type) {
      case 'SESSION_STARTED':
        setSessionId(session_id);
        console.log('[Monitoring] Session started', session_id);
        break;
      case 'SESSION_CONFLICT':
        setError(message || 'Session conflict');
        setState(MonitoringState.ERROR);
        break;
      case 'SESSION_CLOSED':
        if (session_id === sessionId) {
          clearTimeout(stopAckTimer.current);
          setSessionId(null);
          setState(MonitoringState.STOPPED);
          disconnect();
        }
        break;
      case 'ERROR':
        setError(message || 'Unknown error');
        setState(MonitoringState.ERROR);
        break;
      default:
        break;
    }
  }, [lastMessage, sessionId, disconnect]);

  // ---------- Cleanup on unmount ----------
  useEffect(() => {
    return () => {
      stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
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
    sessionId,
  };
}
