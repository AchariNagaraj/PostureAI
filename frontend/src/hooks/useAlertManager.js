// src/hooks/useAlertManager.js
import { useEffect, useRef, useState, useCallback } from 'react';
import { useUI } from '../state/store';

/**
 * Hook to manage alert events coming from the WebSocket.
 * Handles 3 types of notifications of choice for sustained bad posture:
 * 1) System Browser/OS Notification (notificationEnabled)
 * 2) Audio Beep Sound (soundEnabled)
 * 3) Voice Speech Message (voiceEnabled)
 */
export default function useAlertManager(lastMessage) {
  const {
    voiceEnabled,
    setVoiceEnabled,
    notificationEnabled,
    setNotificationEnabled,
    soundEnabled,
    setSoundEnabled,
    voiceVolume,
  } = useUI();

  const [currentAlert, setCurrentAlert] = useState(null);
  const lastAlertIdRef = useRef(null);
  const lastVoiceTimeRef = useRef(0);
  const VOICE_COOLDOWN_MS = 4000;

  const toggleVoice = useCallback(() => {
    const next = !voiceEnabled;
    setVoiceEnabled(next);
    try { localStorage.setItem('voiceEnabled', JSON.stringify(next)); } catch (e) {}
  }, [voiceEnabled, setVoiceEnabled]);

  const toggleSound = useCallback(() => {
    const next = !soundEnabled;
    setSoundEnabled(next);
    try { localStorage.setItem('soundEnabled', JSON.stringify(next)); } catch (e) {}
  }, [soundEnabled, setSoundEnabled]);

  const toggleNotification = useCallback(() => {
    const next = !notificationEnabled;
    if (next && typeof window !== 'undefined' && 'Notification' in window && Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
    setNotificationEnabled(next);
    try { localStorage.setItem('notificationEnabled', JSON.stringify(next)); } catch (e) {}
  }, [notificationEnabled, setNotificationEnabled]);

  // 1. Audio Beep Sound
  const playBeep = useCallback(() => {
    if (!soundEnabled || typeof window === 'undefined') return;
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();

      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(880, ctx.currentTime);
      gain1.gain.setValueAtTime(0.15, ctx.currentTime);
      gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(ctx.currentTime);
      osc1.stop(ctx.currentTime + 0.15);

      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(1174.66, ctx.currentTime + 0.2);
      gain2.gain.setValueAtTime(0.15, ctx.currentTime + 0.2);
      gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(ctx.currentTime + 0.2);
      osc2.stop(ctx.currentTime + 0.4);
    } catch (e) {
      console.warn('[AudioContext Beep]', e);
    }
  }, [soundEnabled]);

  // 2. System OS/Browser Notification
  const triggerSystemNotification = useCallback((title, body) => {
    if (!notificationEnabled || typeof window === 'undefined' || !('Notification' in window)) return;
    if (Notification.permission === 'granted') {
      new Notification(title, { body, icon: '/favicon.ico' });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then((perm) => {
        if (perm === 'granted') {
          new Notification(title, { body, icon: '/favicon.ico' });
        }
      });
    }
  }, [notificationEnabled]);

  // 3. Voice Speech Message
  const speak = useCallback((msg) => {
    if (!voiceEnabled || typeof window === 'undefined' || !window.speechSynthesis) return;
    const now = Date.now();
    if (now - lastVoiceTimeRef.current < VOICE_COOLDOWN_MS) return;
    lastVoiceTimeRef.current = now;
    const utter = new SpeechSynthesisUtterance(msg);
    utter.volume = voiceVolume ?? 0.7;
    window.speechSynthesis.speak(utter);
  }, [voiceEnabled, voiceVolume]);

  const dismiss = useCallback(() => setCurrentAlert(null), []);

  // Keep a ref to the latest overall posture status (GOOD, MODERATE, BAD)
  const latestOverallStatusRef = useRef('UNKNOWN');

  useEffect(() => {
    if (!lastMessage) return;
    const payload = lastMessage.payload;
    if (!payload || typeof payload !== 'object') return;

    // Update the latest overall posture status from any message that carries it
    if (payload.posture_evaluation && typeof payload.posture_evaluation.overall_status === 'string') {
      latestOverallStatusRef.current = payload.posture_evaluation.overall_status;
      // Clear any existing alert if posture is no longer BAD to prevent stale notification UI
      if (latestOverallStatusRef.current !== 'BAD' && currentAlert) {
        setCurrentAlert(null);
      }
    }

    if (lastMessage.type === 'ALERT') {
      const { timestamp, alert_type, posture } = payload;
      if (timestamp == null) return;
      const id = `${alert_type || posture || ''}-${timestamp}`;
      if (lastAlertIdRef.current === id) return;
      // Only proceed if the current overall status is BAD
      if (latestOverallStatusRef.current !== 'BAD') return;
      lastAlertIdRef.current = id;
      setCurrentAlert(payload);

      const msg = payload.voice_message || payload.message || "You're compromising with your posture. Please correct your posture.";

      // Trigger user-selected notification channels for sustained bad posture
      playBeep();
      triggerSystemNotification('PostureAI Sustained Bad Posture Alert', msg);
      speak(msg);
    } else if (payload.voice_message) {
      const id = `VOICE-${payload.voice_message}`;
      if (lastAlertIdRef.current !== id) {
        lastAlertIdRef.current = id;
        speak(payload.voice_message);
      }
    }
  }, [lastMessage, speak, playBeep, triggerSystemNotification]);

  // Initialise settings from localStorage on mount
  useEffect(() => {
    try {
      const storedVoice = localStorage.getItem('voiceEnabled');
      if (storedVoice !== null) setVoiceEnabled(JSON.parse(storedVoice));

      const storedSound = localStorage.getItem('soundEnabled');
      if (storedSound !== null) setSoundEnabled(JSON.parse(storedSound));

      const storedNotif = localStorage.getItem('notificationEnabled');
      if (storedNotif !== null) setNotificationEnabled(JSON.parse(storedNotif));
    } catch (e) {}
  }, []);

  return {
    currentAlert,
    dismiss,
    voiceEnabled,
    toggleVoice,
    soundEnabled,
    toggleSound,
    notificationEnabled,
    toggleNotification,
  };
}
