import React, { useState, useRef, useEffect } from 'react';

import PropertyCard from './components/PropertyCard';
import BookingOptions from './components/BookingOptions';
import VoiceButton from './components/VoiceButton';
import TalkModeButton from './components/TalkModeButton';
import { useVoice } from './hooks/useVoice';
import { generateAirbnbUrls, openInNewTab } from './utils/airbnb-urls';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface SearchResult {
  title: string;
  price: string;
  rating: string;
  link: string;
  source: string;
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hi! I'm Alex, your AI travel assistant from Condfind. I'm here to help you find the perfect Airbnb for your next trip! Where are you planning to stay?",
      sender: 'ai',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [showPropertySelection, setShowPropertySelection] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<SearchResult | null>(null);
  const [showBookingOptions, setShowBookingOptions] = useState(false);
  const [bookingUrls, setBookingUrls] = useState<{
    messageHostUrl: string;
    bookingUrl: string;
    roomId: string | null;
  } | null>(null);
  
  // Voice functionality state
  const [currentLanguage, setCurrentLanguage] = useState('en-US');
  const [isTalkMode, setIsTalkMode] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Voice hook with handlers
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
    continuous: isTalkMode,
    interimResults: true,
    onResult: (finalTranscript) => {
      console.log('Voice result:', finalTranscript);
      if (finalTranscript.trim()) {
        setInputValue(finalTranscript);
        // Auto-send in talk mode after a brief delay
        if (isTalkMode) {
          setTimeout(() => {
            handleSendMessage(finalTranscript.trim());
          }, 500);
        }
      }
    },
    onEnd: () => {
      console.log('Voice recognition ended');
      // Restart listening in talk mode only if AI is not speaking
      if (isTalkMode && !isSpeaking && !isLoading) {
        console.log('Restarting listening in talk mode...');
        setTimeout(() => {
          startListening();
        }, 1500); // Increased delay to prevent rapid restarts
      }
    }
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, searchResults, showPropertySelection, showBookingOptions]);

  const handleSendMessage = async (input?: string) => {
    const messageText = input || inputValue;
    if (!messageText.trim() || isLoading) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Reset previous search state
    setSearchResults([]);
    setShowPropertySelection(false);
    setSelectedProperty(null);
    setShowBookingOptions(false);
    setBookingUrls(null);

    try {
      // Format conversation history for backend
      const conversationHistory = messages.map(msg => ({
        text: msg.text,
        sender: msg.sender
      }));

      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: messageText,
          conversation_history: conversationHistory
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from server');
      }

      const data = await response.json();

      const botMessage: Message = {
        id: messages.length + 2,
        text: data.response || 'I apologize, but I encountered an error processing your request.',
        sender: 'ai',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);

      // Speak the AI response if in talk mode or voice was used
      if (isTalkMode || input) {
        speak(botMessage.text);
      }

      // Handle search results
      if (data.search_results && data.search_results.length > 0) {
        setSearchResults(data.search_results);
        setShowPropertySelection(true);
      }

    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: messages.length + 2,
        text: 'Sorry, I encountered an error while processing your request. Please try again.',
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      
      if (isTalkMode || input) {
        speak(errorMessage.text);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handlePropertySelect = async (property: SearchResult, index: number) => {
    setSelectedProperty(property);
    
    // Extract search parameters from conversation for URL generation
    const searchParams = {
      guests: 2, // Could extract from conversation history
      check_in: '2025-05-31', // Could extract from conversation
      check_out: '2025-06-03'  // Could extract from conversation
    };
    
    // Generate proper URLs with the correct patterns
    const urls = generateAirbnbUrls(property.link, searchParams);
    console.log('Generated URLs with search params:', urls, searchParams);
    setBookingUrls(urls);

    // Show booking options immediately
    setShowBookingOptions(true);

    try {
      // Call backend to handle property selection and get better URLs
      const response = await fetch('http://localhost:8000/choose-property', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          property,
          search_params: searchParams
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Backend response:', data);
        
        // Add confirmation message
        const confirmationMessage: Message = {
          id: messages.length + 1,
          text: data.message,
          sender: 'ai',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, confirmationMessage]);
        
        // Update URLs from backend response if available
        if (data.urls && (data.urls.message_host_url || data.urls.booking_url)) {
          console.log('Updating URLs from backend:', data.urls);
          const mappedUrls = {
            messageHostUrl: data.urls.message_host_url || urls.messageHostUrl,
            bookingUrl: data.urls.booking_url || urls.bookingUrl,
            roomId: data.urls.room_id || urls.roomId
          };
          console.log('Final URLs:', mappedUrls);
          setBookingUrls(mappedUrls);
        }
      } else {
        console.error('Backend response error:', response.status);
      }
    } catch (error) {
      console.error('Error processing property selection:', error);
    }
  };

  const handleMessageHost = () => {
    if (bookingUrls?.messageHostUrl) {
      openInNewTab(bookingUrls.messageHostUrl);
      
      // Add feedback message
      const feedbackMessage: Message = {
        id: messages.length + 1,
        text: "🚀 Opening the Airbnb property page in a new tab! You can find the 'Contact Host' or messaging options on the property page to ask any questions about amenities, check-in process, or local recommendations.",
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, feedbackMessage]);
    }
  };

  const handleBookNow = () => {
    if (bookingUrls?.bookingUrl) {
      openInNewTab(bookingUrls.bookingUrl);
      
      // Add feedback message
      const feedbackMessage: Message = {
        id: messages.length + 1,
        text: "🏠 Opening the Airbnb property page in a new tab! You can complete your reservation by clicking the booking options on the property page. Don't forget to review the cancellation policy and house rules before booking.",
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, feedbackMessage]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  // Voice-specific handlers
  const handleToggleTalkMode = () => {
    if (isTalkMode) {
      // Exit talk mode
      setIsTalkMode(false);
      stopListening();
      stopSpeaking();
    } else {
      // Enter talk mode
      setIsTalkMode(true);
      startListening();
    }
  };

  const handleLanguageSwitch = () => {
    const newLanguage = currentLanguage === 'en-US' ? 'ru-RU' : 'en-US';
    setCurrentLanguage(newLanguage);
    switchLanguage(newLanguage);
  };

  const handleVoicePropertySelect = (index: number) => {
    if (searchResults[index]) {
      handlePropertySelect(searchResults[index], index);
      if (isTalkMode) {
        speak(`Selected property ${index + 1}: ${searchResults[index].title}`);
      }
    }
  };

  // Voice command processing
  useEffect(() => {
    if (transcript && !isLoading && !isSpeaking) {
      // Process voice commands only for specific command patterns
      const command = transcript.toLowerCase().trim();
      
      // Property selection commands - only when we have search results
      if (searchResults.length > 0) {
        const propertyMatch = command.match(/(?:select|choose|pick|book)\s+(?:property\s+)?(\d+|first|second|third)/);
        if (propertyMatch) {
          let index = 0;
          const indexStr = propertyMatch[1];
          if (indexStr === 'first') index = 0;
          else if (indexStr === 'second') index = 1;
          else if (indexStr === 'third') index = 2;
          else index = parseInt(indexStr) - 1;
          
          if (index >= 0 && index < searchResults.length) {
            console.log('Voice command: selecting property', index + 1);
            handleVoicePropertySelect(index);
            return;
          }
        }
      }

      // Navigation commands
      if (command.includes('go back') || command.includes('back')) {
        console.log('Voice command: going back');
        setShowPropertySelection(false);
        setShowBookingOptions(false);
        if (isTalkMode) speak("Going back to search");
        return;
      }

      // Language switch commands
      if (command.includes('switch language') || command.includes('change language')) {
        console.log('Voice command: switching language');
        handleLanguageSwitch();
        const newLang = currentLanguage === 'en-US' ? 'Russian' : 'English';
        if (isTalkMode) speak(`Switching to ${newLang}`);
        return;
      }
    }
  }, [transcript, searchResults, isTalkMode, currentLanguage, isLoading, isSpeaking]);

  // Update scroll effect to include voice state
  useEffect(() => {
    scrollToBottom();
  }, [messages, searchResults, showPropertySelection, showBookingOptions, transcript]);

  return (
    <div className="min-h-screen bg-gray-100 p-4 flex items-center justify-center w-full">
      <div className="w-full max-w-sm sm:max-w-md md:max-w-4xl lg:max-w-6xl xl:max-w-7xl h-[600px] md:h-[700px] lg:h-[800px] bg-white shadow-xl rounded-lg flex flex-col">
        {/* Header */}
        <header className="bg-blue-600 text-white p-6 lg:p-8 rounded-t-lg flex-shrink-0">
          <h1 className="text-3xl lg:text-4xl xl:text-5xl font-bold text-center">Condfind</h1>
          <p className="text-center text-sm lg:text-base">Your AI Assistant for Finding the Perfect Stay</p>
        </header>

        {/* Context Window (Chat Area) */}
        <main className="flex-1 p-6 lg:p-8 space-y-4 overflow-y-auto">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-2xl px-4 py-2 rounded-2xl text-sm md:text-base ${
                  msg.sender === 'user' 
                    ? 'bg-blue-500 text-white rounded-br-md' 
                    : 'bg-gray-200 text-gray-800 rounded-bl-md'
                }`}
              >
                <div className="whitespace-pre-line">{msg.text}</div>
                <div className="text-xs opacity-75 mt-1">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-200 text-gray-800 rounded-bl-md px-4 py-2 rounded-2xl">
                <div className="text-sm animate-pulse">Alex is typing...</div>
              </div>
            </div>
          )}

          {/* Search Results */}
          {showPropertySelection && searchResults.length > 0 && (
            <div className="w-full">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-4">
                <h3 className="text-lg font-bold text-gray-800 mb-2">🏡 Found {searchResults.length} Great Options!</h3>
                <p className="text-gray-600 text-sm">Click on any property to select it and proceed with booking options:</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {searchResults.map((result, index) => (
                  <PropertyCard
                    key={index}
                    property={result}
                    index={index}
                    onSelect={handlePropertySelect}
                    isSelected={selectedProperty?.link === result.link}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Booking Options */}
          {showBookingOptions && selectedProperty && (
            <div className="w-full">
              <BookingOptions
                selectedProperty={selectedProperty}
                onMessageHost={handleMessageHost}
                onBookNow={handleBookNow}
                messageHostUrl={bookingUrls?.messageHostUrl}
                bookingUrl={bookingUrls?.bookingUrl}
                isLoading={!bookingUrls}
              />
            </div>
          )}

          <div ref={messagesEndRef} />
        </main>

        {/* Input Area */}
        <footer className="p-4 lg:p-6 border-t border-gray-200 bg-gray-50 rounded-b-lg flex-shrink-0">
          {/* Voice Status & Controls Row */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <TalkModeButton
                isTalkMode={isTalkMode}
                isListening={isListening}
                isSpeaking={isSpeaking}
                isSupported={voiceSupported}
                onToggleTalkMode={handleToggleTalkMode}
              />
              
              {voiceSupported && (
                <button
                  onClick={handleLanguageSwitch}
                  className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded-full hover:bg-gray-300 transition-colors"
                  title="Switch language"
                >
                  {currentLanguage === 'en-US' ? '🇺🇸 EN' : '🇷🇺 RU'}
                </button>
              )}
            </div>

            {/* Voice status */}
            {(isListening || isSpeaking || transcript) && (
              <div className="text-xs text-gray-600">
                {isListening && "🎤 Listening..."}
                {isSpeaking && "🔊 AI Speaking..."}
                {transcript && !isListening && !isSpeaking && "✓ Voice detected"}
              </div>
            )}
          </div>

          {/* Transcript Display */}
          {transcript && (
            <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-xs text-blue-600 mb-1">Voice Input:</div>
              <div className="text-sm text-blue-800">{transcript}</div>
            </div>
          )}

          {/* Input Row */}
          <div className="flex items-center space-x-3 lg:space-x-4">
            <VoiceButton
              isListening={isListening}
              isProcessing={isProcessing}
              isSpeaking={isSpeaking}
              isSupported={voiceSupported}
              error={voiceError}
              onToggleListening={toggleListening}
              onStopSpeaking={stopSpeaking}
            />
            
            <input 
              type="text" 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                isListening ? "Listening..." :
                isSpeaking ? "AI is speaking..." :
                isLoading ? "Alex is thinking..." : 
                "Tell me what you're looking for..."
              }
              disabled={isLoading}
              className="flex-1 p-3 lg:p-4 text-black text-sm md:text-base border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none disabled:opacity-50 disabled:cursor-not-allowed"
            />
            
            <button 
              aria-label="Send message" 
              onClick={() => handleSendMessage()}
              disabled={isLoading || inputValue.trim() === ''}
              className="p-3 lg:p-4 text-2xl hover:bg-gray-200 rounded-full focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🔍
            </button>
          </div>

          {/* Voice Error Display */}
          {voiceError && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
              Voice Error: {voiceError}
            </div>
          )}
        </footer>
      </div>
    </div>
  );
};

export default App;
