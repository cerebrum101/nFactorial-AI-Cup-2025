import { useState } from 'react'

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  searchResults?: SearchResult[];
}

interface SearchResult {
  title: string;
  price: string;
  rating: string;
  link: string;
  source: string;
}

function App() {
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  // Start with an initial AI greeting
  const [messages, setMessages] = useState<Message[]>([
    { 
      id: 1, 
      text: "Hi! I'm Alex, your AI travel assistant from Condfind. I'm here to help you find the perfect Airbnb for your next trip! Where are you planning to stay?", 
      sender: 'ai' 
    },
  ])

  const sendMessageToBackend = async (userMessage: string, conversationHistory: Message[]) => {
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_history: conversationHistory.map(msg => ({
            text: msg.text,
            sender: msg.sender
          }))
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        text: data.response,
        searchResults: data.search_results
      };
    } catch (error) {
      console.error('Error calling backend:', error);
      return {
        text: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
        searchResults: null
      };
    }
  };

  const handleSend = async () => {
    if (inputValue.trim() === '' || isLoading) return

    const userMessage = inputValue.trim()
    const newUserMessage: Message = { 
      id: Date.now(), 
      text: userMessage, 
      sender: 'user' 
    }

    // Add user message immediately
    const updatedMessages = [...messages, newUserMessage]
    setMessages(updatedMessages)
    setInputValue('')
    setIsLoading(true)

    // Add typing indicator
    const typingIndicator: Message = {
      id: Date.now() + 1,
      text: "Alex is typing...",
      sender: 'ai'
    }
    setMessages([...updatedMessages, typingIndicator])

    try {
      // Send to backend (exclude the typing indicator from history)
      const response = await sendMessageToBackend(userMessage, updatedMessages)
      
      // Replace typing indicator with actual response
      const aiMessage: Message = {
        id: Date.now() + 2,
        text: response.text,
        sender: 'ai',
        searchResults: response.searchResults
      }

      setMessages([...updatedMessages, aiMessage])
    } catch (error) {
      // Remove typing indicator and show error message
      const errorMessage: Message = {
        id: Date.now() + 2,
        text: "I'm sorry, something went wrong. Please try again.",
        sender: 'ai'
      }
      setMessages([...updatedMessages, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const renderSearchResults = (results: SearchResult[]) => {
    return (
      <div className="mt-4 space-y-3">
        <div className="text-sm font-semibold text-gray-600 border-t pt-3">
          🏠 Search Results:
        </div>
        {results.map((result, index) => (
          <div key={index} className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="font-semibold text-gray-800 mb-1">{result.title}</div>
            <div className="text-sm text-gray-600 mb-2">
              💰 {result.price} • ⭐ {result.rating}
            </div>
            {result.link && (
              <a 
                href={result.link} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-block bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
              >
                View on Airbnb →
              </a>
            )}
          </div>
        ))}
      </div>
    );
  };

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
                    : msg.text === 'Alex is typing...'
                    ? 'bg-gray-300 text-gray-600 rounded-bl-md italic animate-pulse'
                    : 'bg-gray-200 text-gray-800 rounded-bl-md'
                }`}
              >
                <div>{msg.text}</div>
                {msg.searchResults && msg.searchResults.length > 0 && renderSearchResults(msg.searchResults)}
              </div>
            </div>
          ))}
        </main>

        {/* Input Area */}
        <footer className="p-4 lg:p-6 border-t border-gray-200 bg-gray-50 rounded-b-lg flex-shrink-0 text-black">
          <div className="flex items-center space-x-3 lg:space-x-4">
            <button 
              aria-label="Voice input" 
              className="p-3 lg:p-4 text-2xl hover:bg-gray-200 rounded-full focus:outline-none transition-colors disabled:opacity-50"
              disabled={isLoading}
            >
              🎤
            </button>
            <input 
              type="text" 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isLoading ? "Alex is thinking..." : "Tell me what you're looking for..."}
              disabled={isLoading}
              className="flex-1 p-3 lg:p-4 text-sm md:text-base border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button 
              aria-label="Search" 
              onClick={handleSend}
              disabled={isLoading || inputValue.trim() === ''}
              className="p-3 lg:p-4 text-2xl hover:bg-gray-200 rounded-full focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🔍
            </button>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default App
