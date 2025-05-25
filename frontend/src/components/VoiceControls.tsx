import React from 'react';
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
  autoProcessedTranscript?: string;
  voiceError: string | null;
  voiceSupported: boolean;
  isWaitingForResponse: boolean;
  onToggleTalkMode: () => void;
  onLanguageSwitch: () => void;
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
  autoProcessedTranscript,
  voiceError,
  voiceSupported,
  isWaitingForResponse,
  onToggleTalkMode,
  onLanguageSwitch
}) => {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  const getStatusMessage = () => {
    if (isTalkMode) {
      if (isListening) return "🎤 Listening for your voice...";
      if (isSpeaking) return "🔊 Alex is speaking...";
      if (isWaitingForResponse) return "⏳ Processing your request...";
      if (isLoading) return "🤔 Alex is thinking...";
      return "🎧 Talk mode active - start speaking";
    }
    return null;
  };

  const statusMessage = getStatusMessage();

  return (
    <footer className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg flex-shrink-0">
      {statusMessage && (
        <div className="mb-3 text-center">
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-full">
            <span className="text-sm font-medium text-blue-800">{statusMessage}</span>
            {isListening && (
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            )}
          </div>
        </div>
      )}

      {isTalkMode && autoProcessedTranscript && autoProcessedTranscript !== inputValue && (
        <div className="mb-2 p-2 bg-green-50 border border-green-200 rounded-lg">
          <div className="text-xs text-green-700 font-medium mb-1">Auto-processed from speech:</div>
          <div className="text-sm text-green-800">"{autoProcessedTranscript}"</div>
        </div>
      )}

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
            title={`Switch language (current: ${currentLanguage === 'en-US' ? 'English' : 'Russian'})`}
          >
            {currentLanguage === 'en-US' ? 'ENG' : 'RUS'}
          </button>
        )}
        
        <input 
          type="text" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            isTalkMode ? (
              isListening ? "Listening..." :
              isSpeaking ? "Alex is speaking..." :
              isWaitingForResponse ? "Processing..." :
              isLoading ? "Alex is thinking..." :
              "🎤 Talk mode active - speak your request"
            ) : (
              isLoading ? "Alex is thinking..." :
              "Click 🎧 to start talk mode, or type your request..."
            )
          }
          disabled={isLoading || (isTalkMode && (isListening || isSpeaking || isWaitingForResponse))}
          readOnly={isTalkMode && !isLoading}
          className={`flex-1 p-3 text-black text-sm md:text-base border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none disabled:opacity-50 disabled:cursor-not-allowed ${
            isTalkMode ? 'bg-blue-50 border-blue-300' : ''
          }`}
        />
        
        {(!isTalkMode || (inputValue.trim() && !isListening && !isSpeaking)) && (
          <button 
            aria-label="Send message" 
            onClick={onSendMessage}
            disabled={isLoading || inputValue.trim() === ''}
            className="p-3 text-xl hover:bg-gray-200 rounded-full focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          >
            🔍
          </button>
        )}
      </div>

      {voiceError && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
          Voice Error: {voiceError}
        </div>
      )}

      {isTalkMode && !isListening && !isSpeaking && !isWaitingForResponse && (
        <div className="mt-2 text-center">
          <div className="text-xs text-gray-500">
            💡 Try: "Find apartments in New York for 2 people under $150" or "Select property 1"
          </div>
        </div>
      )}
    </footer>
  );
};