// src/pages/Settings.jsx
import React from 'react';
import { useUI } from '../state/store';
import { SettingsIcon, VolumeIcon, VolumeMuteIcon, ShieldIcon, LiveIcon } from '../components/Icons';

export default function Settings() {
  const {
    voiceEnabled,
    setVoiceEnabled,
    notificationEnabled,
    setNotificationEnabled,
    soundEnabled,
    setSoundEnabled,
    voiceVolume,
    setVoiceVolume,
  } = useUI();

  const handleVoiceToggle = () => {
    const next = !voiceEnabled;
    setVoiceEnabled(next);
    try {
      localStorage.setItem('voiceEnabled', JSON.stringify(next));
    } catch (e) {}
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
            <SettingsIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">System Settings</h1>
            <p className="text-xs text-slate-400 mt-0.5">Configure monitoring preferences, voice alerts, and UI display options.</p>
          </div>
        </div>
      </div>

      {/* MONITORING PREFERENCES */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <LiveIcon className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-bold text-white">Monitoring Preferences</h2>
        </div>
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
            <div>
              <div className="font-semibold text-slate-200">Default Camera Device</div>
              <div className="text-xs text-slate-400">Primary system webcam input</div>
            </div>
            <span className="px-3 py-1 bg-slate-800 text-slate-300 text-xs font-mono rounded-lg border border-slate-700">
              System Default Webcam
            </span>
          </div>
        </div>
      </div>

      {/* ALERT & NOTIFICATION CHANNELS PREFERENCES */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          {voiceEnabled || soundEnabled || notificationEnabled ? <VolumeIcon className="w-5 h-5 text-cyan-400" /> : <VolumeMuteIcon className="w-5 h-5 text-slate-400" />}
          <h2 className="text-base font-bold text-white">Sustained Bad Posture Alert Channels</h2>
        </div>
        <p className="text-xs text-slate-400">
          Select notification types triggered when sustained bad posture is detected (persistence duration met):
        </p>

        <div className="space-y-4 text-sm">
          {/* 1. System OS / Browser Notification */}
          <div className="flex items-center justify-between p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
            <div>
              <div className="font-semibold text-slate-200">1. System OS & Browser Notification</div>
              <div className="text-xs text-slate-400">Popup browser system notification on sustained bad posture</div>
            </div>
            <button
              onClick={() => {
                const next = !notificationEnabled;
                if (next && typeof window !== 'undefined' && 'Notification' in window && Notification.permission !== 'granted') {
                  Notification.requestPermission();
                }
                setNotificationEnabled(next);
                try { localStorage.setItem('notificationEnabled', JSON.stringify(next)); } catch (e) {}
              }}
              className={`w-12 h-6 rounded-full transition-colors relative p-0.5 focus:outline-none ${
                notificationEnabled ? 'bg-cyan-500' : 'bg-slate-800 border border-slate-700'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full bg-white shadow-md transform transition-transform ${
                  notificationEnabled ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* 2. Audio Beep Sound */}
          <div className="flex items-center justify-between p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
            <div>
              <div className="font-semibold text-slate-200">2. Audio Beep Sound</div>
              <div className="text-xs text-slate-400">Synthetic audio chime beep on sustained posture risk</div>
            </div>
            <button
              onClick={() => {
                const next = !soundEnabled;
                setSoundEnabled(next);
                try { localStorage.setItem('soundEnabled', JSON.stringify(next)); } catch (e) {}
              }}
              className={`w-12 h-6 rounded-full transition-colors relative p-0.5 focus:outline-none ${
                soundEnabled ? 'bg-cyan-500' : 'bg-slate-800 border border-slate-700'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full bg-white shadow-md transform transition-transform ${
                  soundEnabled ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* 3. Voice Speech Message */}
          <div className="flex items-center justify-between p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
            <div>
              <div className="font-semibold text-slate-200">3. Voice Speech Message</div>
              <div className="text-xs text-slate-400">Speech synthesis ("keep your head straight, trunk straight, shoulder aligned")</div>
            </div>
            <button
              onClick={handleVoiceToggle}
              className={`w-12 h-6 rounded-full transition-colors relative p-0.5 focus:outline-none ${
                voiceEnabled ? 'bg-cyan-500' : 'bg-slate-800 border border-slate-700'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full bg-white shadow-md transform transition-transform ${
                  voiceEnabled ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Voice Volume Slider */}
          {voiceEnabled && (
            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-200">Voice Speech Volume</span>
                <span className="font-mono text-cyan-400 font-bold">{Math.round((voiceVolume || 0.7) * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={voiceVolume || 0.7}
                onChange={(e) => setVoiceVolume(parseFloat(e.target.value))}
                className="w-full accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer h-2"
              />
            </div>
          )}
        </div>
      </div>

      {/* DISPLAY & NOTIFICATIONS */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <SettingsIcon className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-bold text-white">Display & UI Layout</h2>
        </div>
        <div className="flex items-center justify-between p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80 text-sm">
          <div>
            <div className="font-semibold text-slate-200">Theme Mode</div>
            <div className="text-xs text-slate-400">Optimized dark mode for monitor viewing</div>
          </div>
          <span className="px-3 py-1 bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 text-xs font-semibold rounded-lg">
            Dark SaaS Slate
          </span>
        </div>
      </div>

      {/* ABOUT SECTION */}
      <div className="p-6 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl space-y-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white">
            <ShieldIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">About PostureAI</h2>
            <p className="text-xs text-slate-400">AI-powered real-time sitting posture monitoring.</p>
          </div>
        </div>
        <div className="p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs text-slate-400 space-y-1">
          <div className="flex justify-between">
            <span>Version</span>
            <span className="font-mono text-slate-200">v1.0.0</span>
          </div>
          <div className="flex justify-between">
            <span>Pipeline Architecture</span>
            <span className="text-slate-200">MediaPipe + Temporal Risk Engine</span>
          </div>
        </div>
      </div>
    </div>
  );
}
