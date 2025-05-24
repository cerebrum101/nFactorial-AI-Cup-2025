import type { Message, ChatResponse, SearchResult, SearchParams } from '../types';

// Use environment variable in production, localhost in development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';       

export const chatService = {
  async sendMessage(message: string, conversationHistory: Omit<Message, 'id' | 'timestamp'>[]): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message,
        conversation_history: conversationHistory
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to get response from server');
    }

    return response.json();
  },

  async selectProperty(property: SearchResult, searchParams: SearchParams) {
    const response = await fetch(`${API_BASE_URL}/choose-property`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        property,
        search_params: searchParams
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to select property');
    }

    return response.json();
  }
};