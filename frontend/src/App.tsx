import React, { useState, useEffect } from 'react';
import { ChatContainer } from './components/ChatContainer';
import { SearchResults } from './components/SearchResults';
import { VoiceControls } from './components/VoiceControls';
import { useChat } from './hooks/useChat';
import { useTalkMode } from './hooks/useTalkMode';
import { usePropertySelection } from './hooks/usePropertySelection';

const App: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const { messages, isLoading, sendMessage, addMessage } = useChat();
  const { 
    searchResults, 
    selectedProperty, 
    showPropertySelection, 
    showBookingOptions, 
    bookingUrls,
    handlePropertySelect,
    handleMessageHost,
    handleBookNow,
    updateSearchResults
  } = usePropertySelection();

  // Voice commands handler
  const handleVoiceCommand = (command: string): boolean => {
    const lowerCommand = command.toLowerCase().trim();
    
    // Property selection commands
    if (showPropertySelection && searchResults.length > 0) {
      // Match patterns like "select property 1", "choose first", "pick number 2", etc.
      const selectPatterns = [
        /(?:select|choose|pick)?\s*(?:property|option|number)?\s*(\d+)/i,
        /(?:select|choose|pick)?\s*(first|second|third|fourth|fifth)/i,
        /(?:I want|I'll take|book)\s*(?:property|option|number)?\s*(\d+)/i,
        /(?:I want|I'll take|book)\s*(first|second|third|fourth|fifth)/i
      ];
      
      for (const pattern of selectPatterns) {
        const match = lowerCommand.match(pattern);
        if (match) {
          let propertyIndex = -1;
          
          if (match[1]) {
            const value = match[1].toLowerCase();
            if (/^\d+$/.test(value)) {
              propertyIndex = parseInt(value) - 1; // Convert to 0-based index
            } else {
              // Handle word numbers
              const wordToNumber: { [key: string]: number } = {
                'first': 0, 'second': 1, 'third': 2, 'fourth': 3, 'fifth': 4
              };
              propertyIndex = wordToNumber[value] ?? -1;
            }
          }
          
          if (propertyIndex >= 0 && propertyIndex < searchResults.length) {
            console.log(`Voice command: selecting property ${propertyIndex + 1}`);
            handlePropertySelect(searchResults[propertyIndex], propertyIndex);
            return true; // Command handled
          }
        }
      }
    }
    
    // Booking action commands
    if (showBookingOptions && selectedProperty) {
      if (/(?:message|contact).*host/i.test(lowerCommand) || 
          /send.*message/i.test(lowerCommand)) {
        console.log('Voice command: message host');
        handleMessageHostWithFeedback();
        return true;
      }
      
      if (/(?:book|reserve|booking)/i.test(lowerCommand)) {
        console.log('Voice command: book now');
        handleBookNowWithFeedback();
        return true;
      }
    }
    
    return false; // Command not handled
  };

  const { 
    isTalkMode, 
    currentLanguage,
    isListening,
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
  } = useTalkMode({
    onVoiceInput: handleVoiceInput,
    onSpeakResponse: (text) => console.log('AI spoke:', text),
    onVoiceCommand: handleVoiceCommand
  });

  const handleSendMessage = async () => {
    const messageText = inputValue;
    if (!messageText.trim() || isLoading) return;

    setInputValue('');
    
    try {
      const data = await sendMessage(messageText);
      
      // ALWAYS speak AI responses in talk mode
      if (isTalkMode && data.response) {
        // Small delay to ensure message is added to chat before speaking
        setTimeout(() => {
          speakResponse(data.response);
        }, 100);
      }

      if (data.search_results) {
        updateSearchResults(data.search_results);
        
        // Announce search results in talk mode
        if (isTalkMode && data.search_results.length > 0) {
          const announcement = `I found ${data.search_results.length} properties for you. You can say "select property 1" or "choose first" to select one.`;
          setTimeout(() => {
            speakResponse(announcement);
          }, 1500); // Delay to let the main response finish
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  function handleVoiceInput(transcript: string) {
    setInputValue(transcript);
    // Shorter delay for better responsiveness
    setTimeout(() => {
      handleSendMessage();
    }, 200);
  }

  const handleMessageHostWithFeedback = () => {
    handleMessageHost();
    const feedbackMessage = "🚀 Opening the Airbnb property page in a new tab! You can find the 'Contact Host' or messaging options on the property page.";
    addMessage({
      text: feedbackMessage,
      sender: 'ai',
      timestamp: new Date()
    });
    
    // Speak feedback in talk mode
    if (isTalkMode) {
      setTimeout(() => {
        speakResponse(feedbackMessage);
      }, 100);
    }
  };

  const handleBookNowWithFeedback = () => {
    handleBookNow();
    const feedbackMessage = "🏠 Opening the Airbnb property page in a new tab! You can complete your reservation on the property page.";
    addMessage({
      text: feedbackMessage,
      sender: 'ai',
      timestamp: new Date()
    });
    
    // Speak feedback in talk mode
    if (isTalkMode) {
      setTimeout(() => {
        speakResponse(feedbackMessage);
      }, 100);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 flex items-center justify-center w-full">
      <div className="w-full max-w-7xl h-[800px] bg-white shadow-xl rounded-lg flex flex-col">
        <header className="bg-blue-600 text-white p-8 rounded-t-lg flex-shrink-0">
          <h1 className="text-5xl font-bold text-center">Condfind</h1>
          <p className="text-center">Your AI Assistant for Finding the Perfect Stay</p>
        </header>

        <ChatContainer messages={messages} isLoading={isLoading} />
        
        {showPropertySelection && (
          <SearchResults
            results={searchResults}
            selectedProperty={selectedProperty}
            showBookingOptions={showBookingOptions}
            bookingUrls={bookingUrls}
            onSelect={handlePropertySelect}
            onMessageHost={handleMessageHostWithFeedback}
            onBookNow={handleBookNowWithFeedback}
          />
        )}
        
        <VoiceControls
          inputValue={inputValue}
          setInputValue={setInputValue}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isTalkMode={isTalkMode}
          currentLanguage={currentLanguage}
          isListening={isListening}
          isSpeaking={isSpeaking}
          transcript={transcript}
          voiceError={voiceError}
          voiceSupported={voiceSupported}
          isWaitingForResponse={isWaitingForResponse}
          onToggleTalkMode={toggleTalkMode}
          onLanguageSwitch={switchLanguageHandler}
          onToggleListening={toggleListening}
          onStopSpeaking={stopSpeaking}
        />
      </div>
    </div>
  );
};

export default App;