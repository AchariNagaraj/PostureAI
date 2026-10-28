// src/state/store.js
import React, { createContext, useContext, useState } from 'react';

const UIContext = createContext(null);

export function UIProvider({ children }) {
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [notificationEnabled, setNotificationEnabled] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [voiceVolume, setVoiceVolume] = useState(0.7);
  const [alertDelay, setAlertDelay] = useState(0); // seconds, placeholder
  const [wsStatus, setWsStatus] = useState('DISCONNECTED');

  const value = {
    voiceEnabled,
    setVoiceEnabled,
    notificationEnabled,
    setNotificationEnabled,
    soundEnabled,
    setSoundEnabled,
    voiceVolume,
    setVoiceVolume,
    alertDelay,
    setAlertDelay,
    wsStatus,
    setWsStatus,
  };

  return React.createElement(UIContext.Provider, { value }, children);
}

export function useUI() {
  const context = useContext(UIContext);
  if (!context) {
    throw new Error('useUI must be used within a UIProvider');
  }
  return context;
}
