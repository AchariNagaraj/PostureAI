// src/hooks/useMonitoring.js
import { useState, useCallback, useEffect } from 'react';
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

export function useMonitoring() {
  const [state, setState] = useState(MonitoringState.IDLE);
  const [error, setError] = useState(null);
  const { stream, status: camStatus, error: camError, start: startCam, stop: stopCam } = useCamera();
  const {
    status: wsStatus,
    error: wsError,
    lastMessage,
    connect,
    disconnect,
    sendFrame,
    selectTarget,
    changeTarget,
    startCalibration,
    finalizeCalibration,
  } = useWebSocket();

  const start = useCallback(() => {
    setState(MonitoringState.STARTING);
    setError(null);
    // Start camera first
    startCam();
  }, [startCam]);

  const stop = useCallback(() => {
    stopCam();
    disconnect();
    setState(MonitoringState.STOPPED);
    setError(null);
  }, [stopCam, disconnect]);

  // React to camera status changes
  useEffect(() => {
    if (camStatus === CameraStatus.ERROR) {
      setError(camError || 'Camera error');
      setState(MonitoringState.ERROR);
      return;
    }
    if (camStatus === CameraStatus.ACTIVE) {
      // Once camera is active, connect WS
      connect();
    }
    if (camStatus === CameraStatus.STOPPED) {
      // Ensure WS is disconnected
      disconnect();
    }
  }, [camStatus, camError, connect, disconnect]);

  // React to WS status changes
  useEffect(() => {
    if (wsStatus === WSStatus.ERROR) {
      setError(wsError || 'WebSocket error');
      setState(MonitoringState.ERROR);
    }
    if (wsStatus === WSStatus.CONNECTED && camStatus === CameraStatus.ACTIVE) {
      setState(MonitoringState.ACTIVE);
    }
    if (wsStatus === WSStatus.DISCONNECTED && state === MonitoringState.ACTIVE) {
      // If WS disconnects while active, go to PAUSED
      setState(MonitoringState.PAUSED);
    }
  }, [wsStatus, wsError, camStatus, state]);

  // Cleanup on unmount
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
  };
}
