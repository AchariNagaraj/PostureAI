// src/components/CameraView.jsx
import React, { useRef, useEffect } from 'react';
import { RefreshIcon, CameraIcon, AlertIcon } from './Icons';

export default function CameraView({
  stream,
  camStatus,
  wsStatus,
  trackingState,
  viewpoint,
  poseValid,
  error,
  lastMessage,
  onFrame,
  onStartCam,
  onReconnectWs,
  onAspectChange,
}) {
  const videoRef = useRef(null);
  const intervalRef = useRef(null);
  const lastSendTimeRef = useRef(0);
  const isPendingRef = useRef(false);

  // Clear pending flag when lastMessage updates or safety timeout passes (500ms)
  useEffect(() => {
    if (lastMessage) {
      isPendingRef.current = false;
    }
  }, [lastMessage]);

  useEffect(() => {
    if (videoRef.current) {
      if (stream) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      } else {
        videoRef.current.srcObject = null;
      }
    }
  }, [stream]);

  // Frame sampling loop (~10 FPS / 100ms interval) with non-deadlocking ACK-gating
  useEffect(() => {
    if (camStatus === 'ACTIVE' && onFrame) {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      intervalRef.current = setInterval(() => {
        const video = videoRef.current;
        if (video && video.readyState >= 2 && video.videoWidth > 0) {
          const vw = video.videoWidth;
          const vh = video.videoHeight;
          const aspect = vw / vh;

          if (onAspectChange) {
            onAspectChange(aspect);
          }

          const now = Date.now();
          // Safety fallback: If pending for > 300ms without response, reset flag to prevent deadlock
          if (isPendingRef.current && (now - lastSendTimeRef.current < 300)) {
            return;
          }

          // Sample canvas maintaining exact video aspect ratio
          const targetWidth = Math.min(640, vw);
          const targetHeight = Math.round(targetWidth / aspect);

          if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
            canvas.width = targetWidth;
            canvas.height = targetHeight;
          }

          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          const dataUrl = canvas.toDataURL('image/jpeg', 0.5);

          isPendingRef.current = true;
          lastSendTimeRef.current = now;
          onFrame(dataUrl);
        }
      }, 100);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      isPendingRef.current = false;
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      isPendingRef.current = false;
    };
  }, [camStatus, onFrame, onAspectChange]);

  // Determine explicit overlay failure state
  const renderOverlay = () => {
    if (camStatus === 'ERROR' || (error && error.toLowerCase().includes('permission'))) {
      return (
        <div className="absolute inset-0 z-20 bg-slate-950/90 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 shadow-xl">
            <CameraIcon className="w-7 h-7" />
          </div>
          <div className="space-y-1 max-w-md">
            <h3 className="text-lg font-bold text-white">Camera Access Required</h3>
            <p className="text-sm text-slate-300">Camera access is required for live posture monitoring.</p>
          </div>
          {onStartCam && (
            <button
              onClick={onStartCam}
              className="inline-flex items-center space-x-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-sm rounded-xl transition shadow-lg shadow-cyan-600/25"
            >
              <RefreshIcon className="w-4 h-4" />
              <span>Try Again</span>
            </button>
          )}
        </div>
      );
    }

    if (camStatus === 'STOPPED' || camStatus === 'INITIALIZING') {
      return (
        <div className="absolute inset-0 z-20 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400">
            <CameraIcon className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-200">
              {camStatus === 'INITIALIZING' ? 'Initializing Camera...' : 'Camera Standby'}
            </h3>
            <p className="text-xs text-slate-400 max-w-sm">
              {camStatus === 'INITIALIZING' ? 'Requesting video feed permissions...' : 'Click "Start Monitoring" to launch real-time webcam analysis.'}
            </p>
          </div>
        </div>
      );
    }

    if (camStatus === 'ACTIVE' && wsStatus === 'DISCONNECTED') {
      return (
        <div className="absolute top-4 left-4 right-4 z-20 bg-amber-950/90 border border-amber-600/40 p-3.5 rounded-xl backdrop-blur-md flex items-center justify-between shadow-xl">
          <div className="flex items-center space-x-3">
            <AlertIcon className="w-5 h-5 text-amber-400" />
            <div>
              <div className="text-xs font-bold text-amber-200 uppercase tracking-wider">Connection Lost</div>
              <div className="text-xs text-amber-300/80">Re-establishing socket stream with PostureAI service...</div>
            </div>
          </div>
          {onReconnectWs && (
            <button
              onClick={onReconnectWs}
              className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-medium text-xs rounded-lg transition"
            >
              Reconnect
            </button>
          )}
        </div>
      );
    }

    if (camStatus === 'ACTIVE' && wsStatus === 'CONNECTING') {
      return (
        <div className="absolute top-4 left-4 right-4 z-20 bg-slate-900/90 border border-slate-700/60 p-3 rounded-xl backdrop-blur-md flex items-center space-x-3 shadow-lg">
          <div className="w-4 h-4 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
          <span className="text-xs font-semibold text-slate-200">Connecting to PostureAI...</span>
        </div>
      );
    }

    if (camStatus === 'ACTIVE' && wsStatus === 'CONNECTED') {
      const returnType = lastMessage?.payload?.person_return_type;

      if (trackingState === 'TARGET_LOST' || (trackingState === 'NO_TARGET' && poseValid === false)) {
        return (
          <div className="absolute top-4 left-4 z-20 px-3.5 py-2 bg-slate-900/95 border border-amber-500/50 rounded-xl backdrop-blur-md flex flex-col space-y-0.5 text-xs shadow-xl">
            <div className="flex items-center space-x-2 text-amber-300 font-bold">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span>Person not detected</span>
            </div>
            <span className="text-slate-400 text-[11px]">Posture monitoring has been paused.</span>
          </div>
        );
      }
      if (trackingState === 'AWAITING_CONFIRMATION') {
        const titleText = returnType === 'SAME_PERSON' ? 'Person detected again.' : 'New person detected.';
        return (
          <div className="absolute top-4 left-4 z-20 px-3.5 py-2 bg-slate-900/95 border border-cyan-500/50 rounded-xl backdrop-blur-md flex flex-col space-y-0.5 text-xs shadow-xl">
            <div className="flex items-center space-x-2 text-cyan-300 font-bold">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span>{titleText}</span>
            </div>
            <span className="text-slate-300 text-[11px]">Do you want to continue monitoring?</span>
          </div>
        );
      }
      if (trackingState === 'NO_PERSON') {
        return (
          <div className="absolute top-4 left-4 z-20 px-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-xl backdrop-blur-md flex items-center space-x-2 text-xs text-slate-300 shadow-md">
            <span className="w-2 h-2 rounded-full bg-slate-400 animate-ping" />
            <span>Person not detected — Monitoring paused</span>
          </div>
        );
      }
      if (trackingState === 'MULTIPLE_PEOPLE') {
        return (
          <div className="absolute top-4 left-4 z-20 px-3 py-1.5 bg-amber-950/90 border border-amber-600/50 rounded-xl backdrop-blur-md flex items-center space-x-2 text-xs text-amber-300 shadow-md">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
            <span>Multiple people detected — Select target person</span>
          </div>
        );
      }
      if (viewpoint === 'UNKNOWN') {
        return (
          <div className="absolute top-4 left-4 z-20 px-3 py-1.5 bg-indigo-950/90 border border-indigo-600/50 rounded-xl backdrop-blur-md flex items-center space-x-2 text-xs text-indigo-300 shadow-md">
            <span>Viewpoint uncertain — face camera for optimal analysis</span>
          </div>
        );
      }
      if (poseValid === false) {
        return (
          <div className="absolute top-4 left-4 z-20 px-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-xl backdrop-blur-md flex items-center space-x-2 text-xs text-slate-300 shadow-md">
            <span>Posture monitoring paused — waiting for pose</span>
          </div>
        );
      }
    }

    return null;
  };

  return (
    <div className="relative w-full h-[460px] sm:h-[520px] max-h-[70vh] bg-[#05080e] rounded-2xl overflow-hidden flex items-center justify-center border border-slate-800/80 shadow-2xl group">
      <video
        ref={videoRef}
        className="w-full h-full object-contain bg-black"
        muted
        playsInline
      />
      {renderOverlay()}
    </div>
  );
}
