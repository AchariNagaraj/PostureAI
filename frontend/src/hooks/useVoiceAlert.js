// src/hooks/useVoiceAlert.js
import { useCallback } from 'react';
import { useUI } from '../state/store';

export default function useVoiceAlert() {
  const {
    voiceEnabled,
    setVoiceEnabled,
    voiceVolume,
  } = useUI();

  const speak = useCallback(
    (message) => {
      if (!voiceEnabled || typeof window === 'undefined') return;
      const utter = new SpeechSynthesisUtterance(message);
      utter.volume = voiceVolume;
      window.speechSynthesis.speak(utter);
    },
    [voiceEnabled, voiceVolume]
  );

  return { speak, voiceEnabled, setVoiceEnabled };
}
