import { useState, useRef, useCallback, useEffect } from 'react';
import { useVoice } from './useVoice';

interface UseTalkModeProps {
  onVoiceInput: (transcript: string) => void;
  onSpeakResponse: (text: string) => void;
  onVoiceCommand?: (command: string) => boolean; // Returns true if command was handled
}

export const useTalkMode = ({ onVoiceInput, onSpeakResponse, onVoiceCommand }: UseTalkModeProps) => {
  const [isTalkMode, setIsTalkMode] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState('en-US');
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  
  // Refs to avoid stale closures in timeouts
  const isTalkModeRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const isWaitingForResponseRef = useRef(false);
  const restartTimeoutRef = useRef<number | null>(null);
  const silenceTimeoutRef = useRef<number | null>(null);
  
  // Keep refs in sync
  useEffect(() => {
    isTalkModeRef.current = isTalkMode;
  }, [isTalkMode]);

  useEffect(() => {
    isWaitingForResponseRef.current = isWaitingForResponse;
  }, [isWaitingForResponse]);

  const clearTimeouts = useCallback(() => {
    if (restartTimeoutRef.current) {
      clearTimeout(restartTimeoutRef.current);
      restartTimeoutRef.current = null;
    }
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
  }, []);

  const scheduleRestart = useCallback(() => {
    clearTimeouts();
    
    // Only restart if talk mode is still active and not waiting for response
    restartTimeoutRef.current = setTimeout(() => {
      if (isTalkModeRef.current && !isSpeakingRef.current && !isWaitingForResponseRef.current) {
        console.log('Restarting listening after silence');
        startListening();
      }
    }, 2500); // Increased delay for better turn-taking
  }, []);

  const handleVoiceResult = useCallback((finalTranscript: string) => {
    if (!finalTranscript.trim() || !isTalkModeRef.current) return;
    
    console.log('Voice result:', finalTranscript);
    clearTimeouts();
    
    // Check for voice commands first
    if (onVoiceCommand && onVoiceCommand(finalTranscript.trim())) {
      console.log('Voice command handled, restarting listening');
      scheduleRestart();
      return;
    }
    
    // Regular voice input
    setIsWaitingForResponse(true);
    stopListening();
    onVoiceInput(finalTranscript.trim());
  }, [onVoiceInput, onVoiceCommand, scheduleRestart]);

  const handleVoiceEnd = useCallback(() => {
    console.log('Voice recognition ended');
    
    // Don't restart immediately - wait for potential AI response
    if (isTalkModeRef.current && !isSpeakingRef.current) {
      scheduleRestart();
    }
  }, [scheduleRestart]);

  const {
    isListening,
    isProcessing,
    isSpeaking,
    transcript,
    error: voiceError,
    isSupported: voiceSupported,
    startListening,
    stopListening,
    toggleListening,
    speak,
    stopSpeaking,
    switchLanguage
  } = useVoice({
    language: currentLanguage,
    continuous: true, // Keep continuous for better experience
    interimResults: true,
    onResult: handleVoiceResult,
    onEnd: handleVoiceEnd
  });

  // Track speaking state
  useEffect(() => {
    isSpeakingRef.current = isSpeaking;
    
    if (isSpeaking) {
      // Stop listening while AI is speaking
      clearTimeouts();
      if (isListening) {
        stopListening();
      }
    } else if (isTalkMode && !isListening && !isWaitingForResponse) {
      // AI finished speaking, restart listening after short delay
      scheduleRestart();
    }
  }, [isSpeaking, isTalkMode, isListening, isWaitingForResponse, scheduleRestart, stopListening]);

  const toggleTalkMode = useCallback(() => {
    if (isTalkMode) {
      console.log('Disabling talk mode');
      setIsTalkMode(false);
      setIsWaitingForResponse(false);
      clearTimeouts();
      stopListening();
      stopSpeaking();
    } else {
      console.log('Enabling talk mode');
      setIsTalkMode(true);
      setIsWaitingForResponse(false);
      clearTimeouts();
      // Start listening immediately when talk mode is enabled
      setTimeout(() => startListening(), 100);
    }
  }, [isTalkMode, startListening, stopListening, stopSpeaking, clearTimeouts]);

  const speakResponse = useCallback((text: string) => {
    if (!isTalkMode) return;
    
    console.log('Speaking response in talk mode:', text);
    setIsWaitingForResponse(false);
    clearTimeouts();
    
    // Ensure we stop listening before speaking
    if (isListening) {
      stopListening();
    }
    
    speak(text);
    onSpeakResponse(text);
  }, [isTalkMode, isListening, speak, onSpeakResponse, stopListening, clearTimeouts]);

  const switchLanguageHandler = useCallback(() => {
    const newLanguage = currentLanguage === 'en-US' ? 'ru-RU' : 'en-US';
    setCurrentLanguage(newLanguage);
    switchLanguage(newLanguage);
  }, [currentLanguage, switchLanguage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimeouts();
    };
  }, [clearTimeouts]);

  return {
    isTalkMode,
    currentLanguage,
    isListening,
    isProcessing,
    isSpeaking,
    transcript,
    voiceError,
    voiceSupported,
    isWaitingForResponse,
    toggleTalkMode,
    speakResponse,
    switchLanguageHandler,
    toggleListening,
    stopSpeaking
  };
};