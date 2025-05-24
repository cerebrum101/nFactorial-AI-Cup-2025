import { useState } from 'react';
import type { SearchResult, BookingUrls, SearchParams } from '../types';
import { generateAirbnbUrls, openInNewTab } from '../utils/airbnb-urls';
import { chatService } from '../services/api';

export const usePropertySelection = () => {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [showPropertySelection, setShowPropertySelection] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<SearchResult | null>(null);
  const [showBookingOptions, setShowBookingOptions] = useState(false);
  const [bookingUrls, setBookingUrls] = useState<BookingUrls | null>(null);

  const handlePropertySelect = async (property: SearchResult, index: number) => {
    setSelectedProperty(property);
    
    const searchParams: SearchParams = {
      guests: 2,
      check_in: '2025-05-31',
      check_out: '2025-06-03'
    };
    
    const urls = generateAirbnbUrls(property.link, searchParams);
    setBookingUrls(urls);
    setShowBookingOptions(true);

    try {
      const data = await chatService.selectProperty(property, searchParams);
      
      if (data.urls && (data.urls.message_host_url || data.urls.booking_url)) {
        const mappedUrls: BookingUrls = {
          messageHostUrl: data.urls.message_host_url || urls.messageHostUrl,
          bookingUrl: data.urls.booking_url || urls.bookingUrl,
          roomId: data.urls.room_id || urls.roomId
        };
        setBookingUrls(mappedUrls);
      }
    } catch (error) {
      console.error('Error processing property selection:', error);
    }
  };

  const handleMessageHost = () => {
    if (bookingUrls?.messageHostUrl) {
      openInNewTab(bookingUrls.messageHostUrl);
    }
  };

  const handleBookNow = () => {
    if (bookingUrls?.bookingUrl) {
      openInNewTab(bookingUrls.bookingUrl);
    }
  };

  const updateSearchResults = (results: SearchResult[]) => {
    setSearchResults(results);
    setShowPropertySelection(results.length > 0);
  };

  return {
    searchResults,
    selectedProperty,
    showPropertySelection,
    showBookingOptions,
    bookingUrls,
    handlePropertySelect,
    handleMessageHost,
    handleBookNow,
    updateSearchResults,
    setShowPropertySelection,
    setShowBookingOptions
  };
};