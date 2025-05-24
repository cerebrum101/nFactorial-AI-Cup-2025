export interface Message {
    id: number;
    text: string;
    sender: 'user' | 'ai';
    timestamp: Date;
  }
  
  export interface SearchResult {
    title: string;
    price: string;
    rating: string;
    link: string;
    source: string;
  }
  
  export interface BookingUrls {
    messageHostUrl: string;
    bookingUrl: string;
    roomId: string | null;
  }
  
  export interface SearchParams {
    guests: number;
    check_in: string;
    check_out: string;
  }
  
  export interface ChatResponse {
    response: string;
    search_results?: SearchResult[];
  }