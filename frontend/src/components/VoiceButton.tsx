import React from 'react';

interface VoiceButtonProps {
  isListening: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  isSupported: boolean;
  error: string | null;
  onToggleListening: () => void;
  onStopSpeaking: () => void;
  className?: string;
}

const VoiceButton: React.FC<VoiceButtonProps> = ({
  isListening,
  isProcessing,
  isSpeaking,
  isSupported,
  error,
  onToggleListening,
  onStopSpeaking,
  className = ""
}) => {
  
  const getButtonState = () => {
    if (!isSupported) return 'unsupported';
    if (error) return 'error';
    if (isListening) return 'listening';
    if (isProcessing) return 'processing';
    if (isSpeaking) return 'speaking';
    return 'idle';
  };

  const buttonState = getButtonState();

  const getButtonStyles = () => {
    const baseStyles = "p-3 lg:p-4 text-2xl rounded-full focus:outline-none transition-all duration-300 relative overflow-hidden";
    
    switch (buttonState) {
      case 'listening':
        return `${baseStyles} bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/50`;
      case 'processing':
        return `${baseStyles} bg-blue-500 text-white animate-spin`;
      case 'speaking':
        return `${baseStyles} bg-green-500 text-white animate-pulse`;
      case 'error':
        return `${baseStyles} bg-red-600 text-white`;
      case 'unsupported':
        return `${baseStyles} bg-gray-400 text-gray-600 cursor-not-allowed`;
      default:
        return `${baseStyles} bg-blue-600 text-white hover:bg-blue-700 active:scale-95`;
    }
  };

  const getButtonIcon = () => {
    switch (buttonState) {
      case 'listening':
        return '🎤';
      case 'processing':
        return '⚡';
      case 'speaking':
        return '🔊';
      case 'error':
        return '❌';
      case 'unsupported':
        return '🚫';
      default:
        return '🎤';
    }
  };

  const getTooltipText = () => {
    switch (buttonState) {
      case 'listening':
        return 'Listening... Click to stop';
      case 'processing':
        return 'Processing your voice...';
      case 'speaking':
        return 'AI is speaking... Click to stop';
      case 'error':
        return `Error: ${error}`;
      case 'unsupported':
        return 'Voice not supported in this browser';
      default:
        return 'Click to start voice input';
    }
  };

  const handleClick = () => {
    if (!isSupported || error) return;
    
    if (isSpeaking) {
      onStopSpeaking();
    } else {
      onToggleListening();
    }
  };

  return (
    <div className="relative group">
      <button
        onClick={handleClick}
        disabled={!isSupported}
        className={`${getButtonStyles()} ${className}`}
        title={getTooltipText()}
        aria-label={getTooltipText()}
      >
        {/* Pulsing ring animation for listening state */}
        {isListening && (
          <div className="absolute inset-0 rounded-full border-4 border-red-400 animate-ping"></div>
        )}
        
        {/* Button icon */}
        <span className="relative z-10">
          {getButtonIcon()}
        </span>
      </button>

      {/* Status tooltip */}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-black bg-opacity-80 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap z-20">
        {getTooltipText()}
      </div>

      {/* Error display */}
      {error && (
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-1 bg-red-600 text-white text-xs rounded-lg max-w-xs text-center z-20">
          {error}
        </div>
      )}
    </div>
  );
};

export default VoiceButton; 