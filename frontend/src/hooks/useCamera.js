// src/hooks/useCamera.js
import { useState, useCallback, useRef, useEffect } from 'react';

export const CameraStatus = {
  INITIALIZING: 'INITIALIZING',
  READY: 'READY',
  ACTIVE: 'ACTIVE',
  ERROR: 'ERROR',
  STOPPED: 'STOPPED',
};

export function useCamera() {
  const [status, setStatus] = useState(CameraStatus.STOPPED);
  const [error, setError] = useState(null);
  const [stream, setStream] = useState(null);
  const streamRef = useRef(null);

  const start = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError('Camera API not available');
      setStatus(CameraStatus.ERROR);
      return;
    }
    setStatus(CameraStatus.INITIALIZING);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = mediaStream;
      setStream(mediaStream);
      setStatus(CameraStatus.ACTIVE);
    } catch (e) {
      setError(e.message || 'Permission denied');
      setStatus(CameraStatus.ERROR);
    }
  }, []);

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setStream(null);
    setStatus(CameraStatus.STOPPED);
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    stream,
    status,
    error,
    start,
    stop,
  };
}
