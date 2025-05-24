import React from 'react';

interface SearchResult {
  title: string;
  price: string;
  rating: string;
  link: string;
  source: string;
}

interface BookingOptionsProps {
  selectedProperty: SearchResult;
  onMessageHost: () => void;
  onBookNow: () => void;
  messageHostUrl?: string;
  bookingUrl?: string;
  isLoading?: boolean;
}

const BookingOptions: React.FC<BookingOptionsProps> = ({
  selectedProperty,
  onMessageHost,
  onBookNow,
  messageHostUrl,
  bookingUrl,
  isLoading = false
}) => {
  
  // Debug logging
  console.log('BookingOptions URLs:', { messageHostUrl, bookingUrl });
  
  // URL handling with proper generated URLs
  const handleMessageHost = () => {
    // Use the generated message host URL which should now work
    const urlToOpen = messageHostUrl || selectedProperty.link;
    console.log('Message Host clicked, opening:', urlToOpen);
    window.open(urlToOpen, '_blank', 'noopener,noreferrer');
    onMessageHost(); // Still call the original handler for chat updates
  };

  const handleBookNow = () => {
    // Use the generated booking URL which should now work
    const urlToOpen = bookingUrl || selectedProperty.link;
    console.log('Book Now clicked, opening:', urlToOpen);
    window.open(urlToOpen, '_blank', 'noopener,noreferrer');
    onBookNow(); // Still call the original handler for chat updates
  };

  return (
    <div className="booking-options bg-gradient-to-r from-green-400 via-blue-500 to-purple-600 rounded-xl p-6 shadow-xl mt-4">
      {/* Header */}
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-white mb-2">
          🎉 Great Choice!
        </h3>
        <p className="text-white opacity-90 text-lg">
          You selected: <span className="font-semibold">{selectedProperty.title}</span>
        </p>
        <p className="text-white opacity-75 text-sm mt-1">
          What would you like to do next?
        </p>
      </div>

      {/* Property Summary */}
      <div className="bg-white bg-opacity-20 rounded-lg p-4 mb-6">
        <div className="flex justify-between items-center text-white">
          <div>
            <span className="text-lg font-bold">{selectedProperty.price}</span>
          </div>
          <div>
            <span className="text-sm">{selectedProperty.rating}</span>
          </div>
        </div>
      </div>

      {/* Debug Info (remove in production) */}
      {import.meta.env.DEV && (
        <div className="mb-4 p-2 bg-black bg-opacity-20 rounded text-white text-xs">
          <div>Message URL: {messageHostUrl || 'Not set'}</div>
          <div>Booking URL: {bookingUrl || 'Not set'}</div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Message Host Button */}
        <button
          onClick={handleMessageHost}
          disabled={isLoading}
          className={`
            group relative overflow-hidden bg-white bg-opacity-20 backdrop-blur-sm
            border-2 border-white border-opacity-30 rounded-xl p-4 
            text-white font-semibold transition-all duration-300
            hover:bg-opacity-30 hover:scale-105 hover:shadow-lg
            focus:outline-none focus:ring-4 focus:ring-white focus:ring-opacity-30
            disabled:opacity-50 disabled:cursor-not-allowed
            flex flex-col items-center space-y-2
          `}
        >
          <div className="text-3xl group-hover:scale-110 transition-transform duration-300">
            💬
          </div>
          <div className="text-lg font-bold">Message Host</div>
          <div className="text-sm opacity-90 text-center">
            Ask questions about amenities, check-in, location, etc.
          </div>
          
          {/* Hover effect overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-pink-500 to-yellow-500 opacity-0 group-hover:opacity-20 transition-opacity duration-300 rounded-xl" />
        </button>

        {/* Book Now Button */}
        <button
          onClick={handleBookNow}
          disabled={isLoading}
          className={`
            group relative overflow-hidden bg-white bg-opacity-20 backdrop-blur-sm
            border-2 border-white border-opacity-30 rounded-xl p-4 
            text-white font-semibold transition-all duration-300
            hover:bg-opacity-30 hover:scale-105 hover:shadow-lg
            focus:outline-none focus:ring-4 focus:ring-white focus:ring-opacity-30
            disabled:opacity-50 disabled:cursor-not-allowed
            flex flex-col items-center space-y-2
          `}
        >
          <div className="text-3xl group-hover:scale-110 transition-transform duration-300">
            🏠
          </div>
          <div className="text-lg font-bold">Book Now</div>
          <div className="text-sm opacity-90 text-center">
            Proceed to Airbnb to complete your reservation
          </div>
          
          {/* Hover effect overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-blue-500 opacity-0 group-hover:opacity-20 transition-opacity duration-300 rounded-xl" />
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="mt-4 flex items-center justify-center text-white">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-2"></div>
          <span>Getting booking links ready...</span>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 text-center text-white opacity-75 text-sm">
        <p>
          Both options will redirect you to Airbnb.com for the actual booking or messaging.
        </p>
        <p className="mt-1">
          ✨ This ensures secure transactions and direct host communication.
        </p>
      </div>
    </div>
  );
};

export default BookingOptions; 