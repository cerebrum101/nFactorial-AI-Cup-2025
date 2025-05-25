import { useState, useEffect, useRef, useCallback } from 'react';

interface VoiceState {
  isListening: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  transcript: string;
  error: string | null;
  isSupported: boolean;
}

interface UseVoiceOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  onResult?: (transcript: string) => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
}

declare global {
  interface Window {
    webkitSpeechRecognition: any;
    SpeechRecognition: any;
  }
}

export const useVoice = (options: UseVoiceOptions = {}) => {
  const {
    language = 'en-US',
    continuous = false,
    interimResults = true,
    onResult,
    onEnd,
    onError
  } = options;

  // Check browser support once
  const isSupported = typeof window !== 'undefined' && 
    ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window);

  const [voiceState, setVoiceState] = useState<VoiceState>({
    isListening: false,
    isProcessing: false,
    isSpeaking: false,
    transcript: '',
    error: null,
    isSupported
  });

  const recognitionRef = useRef<any>(null);
  const synthesisRef = useRef<SpeechSynthesis | null>(null);
  const isInitializedRef = useRef<boolean>(false);
  const isListeningRef = useRef<boolean>(false);

  // Initialize speech synthesis immediately
  useEffect(() => {
    if (typeof window !== 'undefined') {
      synthesisRef.current = window.speechSynthesis;
    }
  }, []);

  // Initialize speech recognition only when needed
  const initializeRecognition = useCallback(() => {
    if (!isSupported || isInitializedRef.current || recognitionRef.current) {
      return recognitionRef.current;
    }

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.lang = language;

      recognition.onstart = () => {
        console.log('Speech recognition started');
        isListeningRef.current = true;
        setVoiceState(prev => ({ ...prev, isListening: true, isProcessing: false, error: null }));
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        const fullTranscript = finalTranscript || interimTranscript;
        setVoiceState(prev => ({ ...prev, transcript: fullTranscript }));

        if (finalTranscript && onResult) {
          console.log('Final transcript:', finalTranscript);
          onResult(finalTranscript);
        }
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
        isListeningRef.current = false;
        setVoiceState(prev => ({ ...prev, isListening: false, isProcessing: false }));
        if (onEnd) onEnd();
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        isListeningRef.current = false;
        const errorMessage = `Speech recognition error: ${event.error}`;
        setVoiceState(prev => ({ 
          ...prev, 
          error: errorMessage, 
          isListening: false, 
          isProcessing: false 
        }));
        if (onError) onError(errorMessage);
      };

      recognitionRef.current = recognition;
      isInitializedRef.current = true;
      
      return recognition;
    } catch (error) {
      console.error('Failed to initialize speech recognition:', error);
      const errorMessage = `Failed to initialize speech recognition: ${error}`;
      setVoiceState(prev => ({ ...prev, error: errorMessage }));
      return null;
    }
  }, [language, continuous, interimResults, onResult, onEnd, onError, isSupported]);

  // Start listening with proper error handling
  const startListening = useCallback(async () => {
    if (!isSupported) {
      const error = 'Speech recognition not supported in this browser';
      setVoiceState(prev => ({ ...prev, error }));
      console.error(error);
      return;
    }

    // Check if already listening to prevent "already started" error
    if (voiceState.isListening || isListeningRef.current) {
      console.log('Speech recognition is already active, skipping start');
      return;
    }

    try {
      // Stop any ongoing speech
      if (synthesisRef.current) {
        synthesisRef.current.cancel();
      }

      // Request microphone permission first
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
          await navigator.mediaDevices.getUserMedia({ audio: true });
          console.log('Microphone permission granted');
        } catch (permissionError) {
          const error = 'Microphone permission denied. Please allow microphone access.';
          setVoiceState(prev => ({ ...prev, error }));
          console.error('Microphone permission error:', permissionError);
          return;
        }
      }

      const recognition = initializeRecognition();
      if (!recognition) {
        const error = 'Failed to initialize speech recognition';
        setVoiceState(prev => ({ ...prev, error }));
        return;
      }

      // Double-check the recognition state before starting
      if (voiceState.isListening || isListeningRef.current) {
        console.log('Recognition became active during initialization, aborting start');
        return;
      }

      setVoiceState(prev => ({ 
        ...prev, 
        transcript: '', 
        error: null, 
        isProcessing: true,
        isSpeaking: false 
      }));
      
      console.log('Starting speech recognition...');
      recognition.start();
      
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      const errorMessage = `Failed to start listening: ${error}`;
      setVoiceState(prev => ({ ...prev, error: errorMessage, isProcessing: false }));
    }
  }, [isSupported, initializeRecognition]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      console.log('Stopping speech recognition...');
      isListeningRef.current = false;
      recognitionRef.current.stop();
    }
  }, []);

  // Text-to-speech function with robust error handling
  const speak = useCallback((text: string) => {
    if (!synthesisRef.current) return;

    // Cancel any ongoing speech first
    synthesisRef.current.cancel();
    
    // Small delay to ensure cancellation is processed
    setTimeout(() => {
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Set language and speech parameters
      utterance.lang = language;
      utterance.rate = 0.9; // Slightly slower for better clarity
      utterance.pitch = 1;
      utterance.volume = 1;

      // Enhanced event handlers with better error recovery
      utterance.onstart = () => {
        console.log('Speech synthesis started:', text.substring(0, 50) + '...');
        setVoiceState(prev => ({ ...prev, isSpeaking: true, error: null }));
      };

      utterance.onend = () => {
        console.log('Speech synthesis completed normally');
        setVoiceState(prev => ({ ...prev, isSpeaking: false }));
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event.error, 'for text:', text.substring(0, 50));
        
        // Handle different error types
        if (event.error === 'interrupted' || event.error === 'canceled') {
          // User interrupted or browser cancelled - this is normal, don't show error
          console.log('Speech was interrupted (normal behavior)');
          setVoiceState(prev => ({ ...prev, isSpeaking: false, error: null }));
        } else if (event.error === 'network') {
          // Network issue - could retry
          setVoiceState(prev => ({ 
            ...prev, 
            isSpeaking: false, 
            error: 'Network error during speech synthesis' 
          }));
        } else {
          // Other errors - show but don't break the experience
          setVoiceState(prev => ({ 
            ...prev, 
            isSpeaking: false, 
            error: `Speech error: ${event.error}` 
          }));
        }
      };

      // Clear any previous errors before speaking
      setVoiceState(prev => ({ ...prev, error: null }));
      
      try {
        console.log('Starting speech synthesis for:', text.substring(0, 50) + '...');
        synthesisRef.current!.speak(utterance);
      } catch (error) {
        console.error('Error calling speak():', error);
        setVoiceState(prev => ({ 
          ...prev, 
          isSpeaking: false, 
          error: 'Failed to start speech synthesis' 
        }));
      }
    }, 100); // Small delay to ensure clean state
  }, [language]);

  // Enhanced stop speaking with better cleanup
  const stopSpeaking = useCallback(() => {
    if (synthesisRef.current) {
      console.log('Stopping speech synthesis...');
      try {
        synthesisRef.current.cancel();
        setVoiceState(prev => ({ ...prev, isSpeaking: false, error: null }));
      } catch (error) {
        console.error('Error stopping speech:', error);
        // Still update state even if cancel failed
        setVoiceState(prev => ({ ...prev, isSpeaking: false }));
      }
    }
  }, []);

  // Toggle listening
  const toggleListening = useCallback(() => {
    if (voiceState.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [voiceState.isListening, startListening, stopListening]);

  // Switch language
  const switchLanguage = useCallback((newLanguage: string) => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = newLanguage;
      console.log('Switched language to:', newLanguage);
    }
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (synthesisRef.current) {
        synthesisRef.current.cancel();
      }
    };
  }, []);

  return {
    ...voiceState,
    startListening,
    stopListening,
    toggleListening,
    speak,
    stopSpeaking,
    switchLanguage
  };
}; 