import { useState } from 'react';
import type { Message, ChatResponse } from '../types';
import { chatService } from '../services/api';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hi! I'm Alex, your AI travel assistant from Condfind. I'm here to help you find the perfect Airbnb for your next trip! Where are you planning to stay?",
      sender: 'ai',
      timestamp: new Date()
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (messageText: string): Promise<ChatResponse> => {
    const userMessage: Message = {
      id: messages.length + 1,
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const conversationHistory = messages.map(msg => ({
        text: msg.text,
        sender: msg.sender
      }));

      const data = await chatService.sendMessage(messageText, conversationHistory);

      const botMessage: Message = {
        id: messages.length + 2,
        text: data.response || 'I apologize, but I encountered an error processing your request.',
        sender: 'ai',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
      return data;

    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: messages.length + 2,
        text: 'Sorry, I encountered an error while processing your request. Please try again.',
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const addMessage = (message: Omit<Message, 'id'>) => {
    setMessages(prev => [...prev, { ...message, id: prev.length + 1 }]);
  };

  return {
    messages,
    isLoading,
    sendMessage,
    addMessage
  };
};