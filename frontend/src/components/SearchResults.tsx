import React from 'react';
import type { SearchResult } from '../types';
import PropertyCard from './PropertyCard';
import BookingOptions from './BookingOptions';

interface SearchResultsProps {
  results: SearchResult[];
  selectedProperty: SearchResult | null;
  showBookingOptions: boolean;
  bookingUrls: any;
  onSelect: (property: SearchResult, index: number) => void;
  onMessageHost: () => void;
  onBookNow: () => void;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  selectedProperty,
  showBookingOptions,
  bookingUrls,
  onSelect,
  onMessageHost,
  onBookNow
}) => {
  return (
    <div className="w-full p-6 overflow-y-auto flex-shrink-0 max-h-96">
      {results.length > 0 && (
        <>
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-4">
            <h3 className="text-lg font-bold text-gray-800 mb-2">🏡 Found {results.length} Great Options!</h3>
            <p className="text-gray-600 text-sm">Click on any property to select it and proceed with booking options:</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((result, index) => (
              <PropertyCard
                key={index}
                property={result}
                index={index}
                onSelect={onSelect}
                isSelected={selectedProperty?.link === result.link}
              />
            ))}
          </div>

          {showBookingOptions && selectedProperty && (
            <div className="mt-6">
              <BookingOptions
                selectedProperty={selectedProperty}
                onMessageHost={onMessageHost}
                onBookNow={onBookNow}
                messageHostUrl={bookingUrls?.messageHostUrl}
                bookingUrl={bookingUrls?.bookingUrl}
                isLoading={!bookingUrls}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
};