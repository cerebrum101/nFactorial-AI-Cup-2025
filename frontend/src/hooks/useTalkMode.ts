import { useState, useRef, useCallback, useEffect } from 'react';
import { useVoice } from './useVoice';

interface UseTalkModeProps {
  onVoiceInput: (transcript: string, confidence?: number) => void;
  onSpeakResponse: (text: string) => void;
  onVoiceCommand?: (command: string) => boolean; // Returns true if command was handled
}

export const useTalkMode = ({ onVoiceInput, onSpeakResponse, onVoiceCommand }: UseTalkModeProps) => {
  const [isTalkMode, setIsTalkMode] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState('en-US');
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [autoProcessedTranscript, setAutoProcessedTranscript] = useState('');
  
  // Refs to avoid stale closures in timeouts
  const isTalkModeRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const isWaitingForResponseRef = useRef(false);
  const restartTimeoutRef = useRef<number | null>(null);
  const silenceTimeoutRef = useRef<number | null>(null);
  const lastTranscriptRef = useRef<string>('');
  
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

  // Context-aware transcript processing
  const processTranscript = useCallback((transcript: string): string => {
    let processed = transcript.trim();
    
    // Basic cleanup for common speech-to-text errors
    const corrections = [
      // Common misheard words in travel context
      [/\bstanbul\b/gi, 'Istanbul'],
      [/\bmoscow\b/gi, 'Moscow'],
      [/\bnew york\b/gi, 'New York'],
      [/\blondon\b/gi, 'London'],
      [/\bparis\b/gi, 'Paris'],
      [/\btokyo\b/gi, 'Tokyo'],
      
      // Price corrections
      [/\$(\d+)\s*(?:per|a)\s*(?:night|day)/gi, '$$$1 per night'],
      [/(\d+)\s*(?:dollars?|bucks?)\s*(?:per|a)\s*(?:night|day)/gi, '$$$1 per night'],
      [/under\s*(\d+)\s*(?:dollars?|bucks?)/gi, 'under $$$1'],
      [/maximum\s*(\d+)\s*(?:dollars?|bucks?)/gi, 'maximum $$$1'],
      
      // Guest count corrections
      [/(\d+)\s*people/gi, '$1 people'],
      [/(\d+)\s*guests?/gi, '$1 guests'],
      [/for\s*(\d+)/gi, 'for $1'],
      
      // Date corrections
      [/june\s*(\d+)/gi, 'June $1'],
      [/july\s*(\d+)/gi, 'July $1'],
      [/august\s*(\d+)/gi, 'August $1'],
      [/may\s*(\d+)/gi, 'May $1'],
      
      // Common command corrections
      [/select\s*property\s*(\d+)/gi, 'select property $1'],
      [/choose\s*(?:the\s*)?(?:first|1st|one)/gi, 'choose first'],
      [/book\s*(?:this|it|now)/gi, 'book now'],
      [/message\s*(?:the\s*)?host/gi, 'message host'],
    ];
    
    corrections.forEach(([pattern, replacement]) => {
      processed = processed.replace(pattern, replacement as string);
    });
    
    return processed;
  }, []);

  const scheduleRestart = useCallback(() => {
    clearTimeouts();
    
    // Only restart if talk mode is still active and not waiting for response
    restartTimeoutRef.current = setTimeout(() => {
      if (isTalkModeRef.current && !isSpeakingRef.current && !isWaitingForResponseRef.current) {
        console.log('📢 Restarting listening after silence');
        startListening();
      }
    }, 2000); // Reduced delay for more responsive experience
  }, []);

  const handleVoiceResult = useCallback((finalTranscript: string) => {
    if (!finalTranscript.trim() || !isTalkModeRef.current) return;
    
    // Avoid processing the same transcript multiple times
    if (finalTranscript === lastTranscriptRef.current) {
      console.log('📢 Duplicate transcript ignored');
      return;
    }
    lastTranscriptRef.current = finalTranscript;
    
    // Process and improve transcript
    const processedTranscript = processTranscript(finalTranscript);
    setAutoProcessedTranscript(processedTranscript);
    
    console.log('📢 Voice result:', finalTranscript);
    console.log('📢 Processed:', processedTranscript);
    clearTimeouts();
    
    // Check for voice commands first
    if (onVoiceCommand && onVoiceCommand(processedTranscript)) {
      console.log('📢 Voice command handled, restarting listening');
      setIsWaitingForResponse(false); // Clear waiting state
      scheduleRestart();
      return;
    }
    
    // For regular voice input, auto-process without manual correction
    setIsWaitingForResponse(true);
    stopListening();
    
    // Send the processed transcript directly with timeout fallback
    try {
      onVoiceInput(processedTranscript, 0.95); // High confidence since we processed it
      
      // Fallback timeout to clear waiting state if no response comes
      setTimeout(() => {
        if (isWaitingForResponseRef.current) {
          console.log('📢 Timeout: Clearing waiting state after no response');
          setIsWaitingForResponse(false);
          scheduleRestart();
        }
      }, 10000); // 10 second timeout
      
    } catch (error) {
      console.error('📢 Error sending voice input:', error);
      setIsWaitingForResponse(false);
      scheduleRestart();
    }
  }, [onVoiceInput, onVoiceCommand, scheduleRestart, processTranscript]);

  const handleVoiceEnd = useCallback(() => {
    console.log('📢 Voice recognition ended');
    
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

  // Track speaking state with better turn-taking
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
      console.log('📢 AI finished speaking, preparing to listen again');
      scheduleRestart();
    }
  }, [isSpeaking, isTalkMode, isListening, isWaitingForResponse, scheduleRestart, stopListening]);

  const toggleTalkMode = useCallback(() => {
    if (isTalkMode) {
      console.log('📢 Disabling talk mode');
      setIsTalkMode(false);
      setIsWaitingForResponse(false);
      setAutoProcessedTranscript('');
      clearTimeouts();
      stopListening();
      stopSpeaking();
    } else {
      console.log('📢 Enabling talk mode');
      setIsTalkMode(true);
      setIsWaitingForResponse(false);
      setAutoProcessedTranscript('');
      clearTimeouts();
      // Start listening immediately when talk mode is enabled
      setTimeout(() => {
        console.log('📢 Talk mode enabled, starting to listen...');
        startListening();
      }, 200); // Small delay to ensure state is set
    }
  }, [isTalkMode, startListening, stopListening, stopSpeaking, clearTimeouts]);

  const speakResponse = useCallback((text: string) => {
    if (!isTalkMode) return;
    
    console.log('📢 Speaking response in talk mode:', text.substring(0, 50) + '...');
    setIsWaitingForResponse(false);
    clearTimeouts();
    
    // Ensure we stop listening before speaking
    if (isListening) {
      stopListening();
    }
    
    // Clean text for better speech synthesis
    let speakText = text
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
      .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
      .replace(/🎉|🚀|✨|💰|⭐|📍|👥|🏠|🔍|🎤|🔊|⏳/g, '') // Remove emojis
      .replace(/\n+/g, '. ') // Replace newlines with pauses
      .trim();
    
    speak(speakText);
    onSpeakResponse(speakText);
  }, [isTalkMode, isListening, speak, onSpeakResponse, stopListening, clearTimeouts]);

  const switchLanguageHandler = useCallback(() => {
    const newLanguage = currentLanguage === 'en-US' ? 'ru-RU' : 'en-US';
    console.log('📢 Switching language to:', newLanguage);
    setCurrentLanguage(newLanguage);
    switchLanguage(newLanguage);
  }, [currentLanguage, switchLanguage]);

  // Enhanced error handling
  const enhancedVoiceError = voiceError && !voiceError.includes('interrupted') ? voiceError : null;

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
    autoProcessedTranscript, // New: show the processed version
    voiceError: enhancedVoiceError, // Filter out "interrupted" errors
    voiceSupported,
    isWaitingForResponse,
    toggleTalkMode,
    speakResponse,
    switchLanguageHandler,
    toggleListening,
    stopSpeaking
  };
};