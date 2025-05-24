import React from 'react';

interface TalkModeButtonProps {
  isTalkMode: boolean;
  isListening: boolean;
  isSpeaking: boolean;
  isWaitingForResponse?: boolean;
  isSupported: boolean;
  onToggleTalkMode: () => void;
  className?: string;
}

const TalkModeButton: React.FC<TalkModeButtonProps> = ({
  isTalkMode,
  isListening,
  isSpeaking,
  isWaitingForResponse,
  isSupported,
  onToggleTalkMode,
  className = ""
}) => {

  const getButtonStyles = () => {
    const baseStyles = "px-4 py-2 rounded-lg font-medium text-sm transition-all duration-300 flex items-center space-x-2 relative";
    
    if (!isSupported) {
      return `${baseStyles} bg-gray-300 text-gray-500 cursor-not-allowed`;
    }
    
    if (isTalkMode) {
      if (isListening) {
        return `${baseStyles} bg-red-500 text-white shadow-lg animate-pulse ring-2 ring-red-300`;
      } else if (isSpeaking) {
        return `${baseStyles} bg-green-500 text-white shadow-lg animate-pulse ring-2 ring-green-300`;
      } else if (isWaitingForResponse) {
        return `${baseStyles} bg-yellow-500 text-white shadow-lg animate-pulse ring-2 ring-yellow-300`;
      } else {
        return `${baseStyles} bg-blue-600 text-white shadow-lg ring-2 ring-blue-300`;
      }
    }
    
    return `${baseStyles} bg-gray-200 text-gray-700 hover:bg-gray-300 hover:shadow-md`;
  };

  const getButtonIcon = () => {
    if (!isSupported) return '🚫';
    
    if (isTalkMode) {
      if (isListening) return '🎤';
      if (isSpeaking) return '🔊';
      if (isWaitingForResponse) return '⏳';
      return '💬';
    }
    
    return '💬';
  };

  const getButtonText = () => {
    if (!isSupported) return 'Voice Not Supported';
    
    if (isTalkMode) {
      if (isListening) return 'Listening...';
      if (isSpeaking) return 'AI Speaking...';
      if (isWaitingForResponse) return 'Processing...';
      return 'Talk Mode ON';
    }
    
    return 'Start Talk Mode';
  };

  const getTooltipText = () => {
    if (!isSupported) return 'Voice not supported in this browser';
    
    if (isTalkMode) {
      return 'Click to exit talk mode. Say "select property 1" or "choose first" to select properties.';
    }
    
    return 'Start talk mode for hands-free conversation with voice commands';
  };

  return (
    <div className="relative group">
      <button
        onClick={onToggleTalkMode}
        disabled={!isSupported}
        className={`${getButtonStyles()} ${className}`}
        title={getTooltipText()}
        aria-label={getTooltipText()}
      >
        {/* Pulsing dot for active talk mode */}
        {isTalkMode && (
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
        )}
        
        <span>{getButtonIcon()}</span>
        <span>{getButtonText()}</span>
      </button>

      {/* Status indicator */}
      {isTalkMode && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-black bg-opacity-80 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap z-20">
          {isListening ? 'Listening for your voice...' : 
           isSpeaking ? 'AI is speaking...' :
           isWaitingForResponse ? 'Processing your request...' :
           'Talk mode active - try "select property 1" or ask anything'}
        </div>
      )}
    </div>
  );
};

export default TalkModeButton; 