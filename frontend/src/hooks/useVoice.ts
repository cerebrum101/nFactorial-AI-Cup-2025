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
        setVoiceState(prev => ({ ...prev, isListening: false, isProcessing: false }));
        if (onEnd) onEnd();
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
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
      recognitionRef.current.stop();
    }
  }, []);

  // Text-to-speech function
  const speak = useCallback((text: string) => {
    if (!synthesisRef.current) return;

    // Cancel any ongoing speech
    synthesisRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Set language based on current language
    utterance.lang = language;
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      console.log('Speech synthesis started');
      setVoiceState(prev => ({ ...prev, isSpeaking: true }));
    };

    utterance.onend = () => {
      console.log('Speech synthesis ended');
      setVoiceState(prev => ({ ...prev, isSpeaking: false }));
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setVoiceState(prev => ({ 
        ...prev, 
        isSpeaking: false, 
        error: `Speech synthesis error: ${event.error}` 
      }));
    };

    setVoiceState(prev => ({ ...prev, error: null }));
    console.log('Starting speech synthesis...');
    synthesisRef.current.speak(utterance);
  }, [language]);

  // Stop speaking
  const stopSpeaking = useCallback(() => {
    if (synthesisRef.current) {
      console.log('Stopping speech synthesis...');
      synthesisRef.current.cancel();
      setVoiceState(prev => ({ ...prev, isSpeaking: false }));
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