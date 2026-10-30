// src/hooks/useWebSocket.js
import { useState, useEffect, useRef, useCallback } from 'react';

export const WSStatus = {
  CONNECTING: 'CONNECTING',
  CONNECTED: 'CONNECTED',
  DISCONNECTED: 'DISCONNECTED',
  ERROR: 'ERROR',
};

export function useWebSocket(url = null) {
  const [status, setStatus] = useState(WSStatus.DISCONNECTED);
  const [error, setError] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);

  const connect = useCallback(() => {
    const envWsUrl =
      (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_WS_URL) ||
      (typeof process !== 'undefined' && process.env && process.env.VITE_WS_URL);
    const wsUrl = url || envWsUrl || 'ws://localhost:8000/ws';
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      setStatus(WSStatus.CONNECTING);

      ws.onopen = () => {
        setStatus(WSStatus.CONNECTED);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data && data.type) {
            setLastMessage(data);
          }
        } catch (e) {
          // malformed JSON, ignore
        }
      };

      ws.onerror = () => {
        setError('WebSocket error');
        setStatus(WSStatus.ERROR);
      };

      ws.onclose = () => {
        setStatus(WSStatus.DISCONNECTED);
        wsRef.current = null;
      };
    } catch (e) {
      setError(e.message || 'Failed to create WebSocket');
      setStatus(WSStatus.ERROR);
    }
  }, [url]);

  const sendFrame = useCallback((base64Frame, timestamp = null, selectTargetId = null) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload = {
        type: 'FRAME',
        timestamp: timestamp || Date.now() / 1000.0,
        frame: base64Frame,
      };
      if (selectTargetId != null) {
        payload.select_target_id = selectTargetId;
      }
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  const selectTarget = useCallback((targetId) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'SELECT_TARGET',
          target_id: targetId,
        })
      );
    }
  }, []);

  const changeTarget = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'CHANGE_TARGET',
        })
      );
    }
  }, []);

  const startCalibration = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'START_CALIBRATION' }));
    }
  }, []);

  const finalizeCalibration = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'FINALIZE_CALIBRATION' }));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus(WSStatus.DISCONNECTED);
    setLastMessage(null);
    setError(null);
  }, []);

  // Helper to send JSON messages over the WebSocket
  const sendMessage = useCallback((type, payload = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = { type, ...payload };
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    error,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    sendFrame,
    selectTarget,
    changeTarget,
    startCalibration,
    finalizeCalibration,
  };
}
