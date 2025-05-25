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
    <footer className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg flex-shrink-0">
      {/* Status indicator row - only show when there's something to show */}
      {(isListening || isSpeaking || isWaitingForResponse) && (
        <div className="mb-2 text-center">
          <div className="text-xs text-gray-600">
            {isListening && "🎤 Listening..."}
            {isSpeaking && "🔊 AI Speaking..."}
            {isWaitingForResponse && "⏳ Processing..."}
          </div>
        </div>
      )}

      {/* Main input row with all controls */}
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
            className="px-2 py-1 text-xs bg-gray-200 text-white rounded-full hover:bg-gray-300 transition-colors flex-shrink-0"
            title="Switch language"
          >
            {currentLanguage === 'en-US' ? 'ENG' : 'RUS'}
          </button>
        )}

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
          className="flex-1 p-3 text-black text-sm md:text-base border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none disabled:opacity-50 disabled:cursor-not-allowed"
        />
        
        <button 
          aria-label="Send message" 
          onClick={onSendMessage}
          disabled={isLoading || inputValue.trim() === ''}
          className="p-3 text-xl hover:bg-gray-200 rounded-full focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
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