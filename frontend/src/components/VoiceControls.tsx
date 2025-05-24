import React from 'react';
import VoiceButton from './VoiceButton';
import TalkModeButton from './TalkModeButton';

interface VoiceControlsProps {
  inputValue: string;
  setInputValue: (value: string) => void;
  onSendMessage: () => void;
  isLoading: boolean;
  isTalkMode: boolean;
  currentLanguage: string;
  isListening: boolean;
  isSpeaking: boolean;
  transcript: string;
  voiceError: string | null;
  voiceSupported: boolean;
  isWaitingForResponse: boolean;
  onToggleTalkMode: () => void;
  onLanguageSwitch: () => void;
  onToggleListening: () => void;
  onStopSpeaking: () => void;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  inputValue,
  setInputValue,
  onSendMessage,
  isLoading,
  isTalkMode,
  currentLanguage,
  isListening,
  isSpeaking,
  transcript,
  voiceError,
  voiceSupported,
  isWaitingForResponse,
  onToggleTalkMode,
  onLanguageSwitch,
  onToggleListening,
  onStopSpeaking
}) => {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <footer className="p-4 lg:p-6 border-t border-gray-200 bg-gray-50 rounded-b-lg flex-shrink-0">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <TalkModeButton
            isTalkMode={isTalkMode}
            isListening={isListening}
            isSpeaking={isSpeaking}
            isWaitingForResponse={isWaitingForResponse}
            isSupported={voiceSupported}
            onToggleTalkMode={onToggleTalkMode}
          />
          
          {voiceSupported && (
            <button
              onClick={onLanguageSwitch}
              className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded-full hover:bg-gray-300 transition-colors"
              title="Switch language"
            >
              {currentLanguage === 'en-US' ? '🇺🇸 EN' : '🇷🇺 RU'}
            </button>
          )}
        </div>

        {(isListening || isSpeaking || transcript || isWaitingForResponse) && (
          <div className="text-xs text-gray-600">
            {isListening && "🎤 Listening..."}
            {isSpeaking && "🔊 AI Speaking..."}
            {isWaitingForResponse && "⏳ Processing..."}
            {transcript && !isListening && !isSpeaking && !isWaitingForResponse && "✓ Voice detected"}
          </div>
        )}
      </div>

      {transcript && (
        <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-xs text-blue-600 mb-1">Voice Input:</div>
          <div className="text-sm text-blue-800">{transcript}</div>
        </div>
      )}

      <div className="flex items-center space-x-3 lg:space-x-4">
        <VoiceButton
          isListening={isListening}
          isProcessing={false}
          isSpeaking={isSpeaking}
          isSupported={voiceSupported}
          error={voiceError}
          onToggleListening={onToggleListening}
          onStopSpeaking={onStopSpeaking}
        />
        
        <input 
          type="text" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            isListening ? "Listening..." :
            isSpeaking ? "AI is speaking..." :
            isWaitingForResponse ? "Processing your request..." :
            isLoading ? "Alex is thinking..." :
            isTalkMode ? "Talk mode active - speak your request..." :
            "Tell me what you're looking for..."
          }
          disabled={isLoading}
          className="flex-1 p-3 lg:p-4 text-black text-sm md:text-base border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none disabled:opacity-50 disabled:cursor-not-allowed"
        />
        
        <button 
          aria-label="Send message" 
          onClick={onSendMessage}
          disabled={isLoading || inputValue.trim() === ''}
          className="p-3 lg:p-4 text-2xl hover:bg-gray-200 rounded-full focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          🔍
        </button>
      </div>

      {voiceError && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
          Voice Error: {voiceError}
        </div>
      )}
    </footer>
  );
};