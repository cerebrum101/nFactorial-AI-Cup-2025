import React, { useRef, useEffect } from 'react';
import type { Message } from '../types'; 

interface ChatContainerProps {
  messages: Message[];
  isLoading: boolean;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({ messages, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
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

      {isLoading && (
        <div className="flex justify-start">
          <div className="bg-gray-200 text-gray-800 rounded-bl-md px-4 py-2 rounded-2xl">
            <div className="text-sm animate-pulse">Alex is typing...</div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </main>
  );
};