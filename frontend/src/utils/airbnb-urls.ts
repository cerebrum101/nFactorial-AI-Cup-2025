/**
 * Utility functions for manipulating Airbnb URLs to generate
 * message host and booking links
 */

export interface SearchParams {
  guests?: number;
  check_in?: string;
  check_out?: string;
}

/**
 * Extract room ID from Airbnb listing URL
 * Example: https://www.airbnb.com/rooms/12345678 → "12345678"
 */
export const extractRoomId = (airbnbUrl: string): string | null => {
  try {
    console.log('Extracting room ID from URL:', airbnbUrl);
    
    // Handle different Airbnb URL formats
    const patterns = [
      /\/rooms\/(\d+)/, // Standard format
      /listing_(\d+)/, // Alternative format
      /\/(\d+)\?/, // Room ID before query params
    ];

    for (const pattern of patterns) {
      const match = airbnbUrl.match(pattern);
      if (match && match[1]) {
        console.log('Room ID extracted:', match[1]);
        return match[1];
      }
    }

    console.warn('Could not extract room ID from URL:', airbnbUrl);
    return null;
  } catch (error) {
    console.error('Error extracting room ID:', error);
    return null;
  }
};

/**
 * Generate URL for messaging the host
 * This redirects to Airbnb's contact host page
 */
export const generateMessageHostUrl = (roomId: string, searchParams: SearchParams = {}): string => {
  const { guests = 2, check_in, check_out } = searchParams;
  
  // Build query parameters using the working format
  const params = new URLSearchParams();
  params.set('adults', guests.toString());
  
  // Add dates if available (use underscore format for contact host)
  if (check_in) params.set('check_in', check_in);
  if (check_out) params.set('check_out', check_out);
  
  // Default dates if not provided
  if (!check_in || !check_out) {
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    const checkout = new Date(nextWeek);
    checkout.setDate(checkout.getDate() + 3);
    
    params.set('check_in', nextWeek.toISOString().split('T')[0]);
    params.set('check_out', checkout.toISOString().split('T')[0]);
  }

  // Use the exact working format: /contact_host/{room_id}/send_message
  return `https://www.airbnb.com/contact_host/${roomId}/send_message?${params.toString()}`;
};

/**
 * Generate URL for booking the property
 * Includes search parameters like guests and dates
 */
export const generateBookingUrl = (
  roomId: string, 
  searchParams: SearchParams = {}
): string => {
  const { guests = 2, check_in, check_out } = searchParams;
  
  // Build query parameters using the working booking format
  const params = new URLSearchParams();
  params.set('numberOfAdults', guests.toString());
  params.set('guestCurrency', 'USD');
  params.set('productId', roomId);
  params.set('isWorkTrip', 'false');
  params.set('numberOfChildren', '0');
  params.set('numberOfGuests', guests.toString());
  params.set('numberOfInfants', '0');
  params.set('numberOfPets', '0');
  
  // Add dates if available (use no underscore format for booking)
  if (check_in) params.set('checkin', check_in);
  if (check_out) params.set('checkout', check_out);
  
  // Default dates if not provided
  if (!check_in || !check_out) {
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    const checkout = new Date(nextWeek);
    checkout.setDate(checkout.getDate() + 3);
    
    params.set('checkin', nextWeek.toISOString().split('T')[0]);
    params.set('checkout', checkout.toISOString().split('T')[0]);
  }

  // Use the exact working format: /book/stays/{room_id}
  return `https://www.airbnb.com/book/stays/${roomId}?${params.toString()}`;
};

/**
 * Generate both message and booking URLs from a property listing
 */
export const generateAirbnbUrls = (
  listingUrl: string,
  searchParams: SearchParams = {}
) => {
  const roomId = extractRoomId(listingUrl);
  
  if (!roomId) {
    console.warn('Could not extract room ID, using original URL as fallback');
    return {
      messageHostUrl: listingUrl,
      bookingUrl: listingUrl,
      roomId: null,
    };
  }

  return {
    messageHostUrl: generateMessageHostUrl(roomId, searchParams),
    bookingUrl: generateBookingUrl(roomId, searchParams),
    roomId,
  };
};

/**
 * Validate if a URL looks like an Airbnb listing
 */
export const isAirbnbUrl = (url: string): boolean => {
  try {
    const parsedUrl = new URL(url);
    return parsedUrl.hostname.includes('airbnb.com');
  } catch {
    return false;
  }
};

/**
 * Helper function to open URL in new tab safely
 */
export const openInNewTab = (url: string) => {
  window.open(url, '_blank', 'noopener,noreferrer');
}; 