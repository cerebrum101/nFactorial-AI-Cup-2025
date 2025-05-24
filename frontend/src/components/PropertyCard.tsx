import React from 'react';

interface PropertyCardProps {
  property: {
    title: string;
    price: string;
    rating: string;
    link: string;
    source: string;
  };
  index: number;
  onSelect: (property: any, index: number) => void;
  isSelected: boolean;
}

const PropertyCard: React.FC<PropertyCardProps> = ({ property, index, onSelect, isSelected }) => {
  const handleClick = () => {
    onSelect(property, index);
  };

  return (
    <div
      onClick={handleClick}
      className={`
        relative cursor-pointer rounded-lg border-2 transition-all duration-300 transform hover:scale-105 
        ${isSelected 
          ? 'border-green-500 bg-green-50 shadow-lg shadow-green-200' 
          : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-lg'
        }
      `}
      role="button"
      tabIndex={0}
      onKeyPress={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
      aria-label={`Property ${index + 1}: ${property.title}, ${property.price}, Rating ${property.rating}`}
    >
      {/* Selection Number Badge */}
      <div className={`
        absolute -top-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10
        ${isSelected 
          ? 'bg-green-500 text-white shadow-lg' 
          : 'bg-blue-500 text-white shadow-md'
        }
      `}>
        {index + 1}
      </div>

      {/* Selection Checkmark */}
      {isSelected && (
        <div className="absolute top-3 left-3 bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center z-10">
          ✓
        </div>
      )}

      {/* Gradient Background */}
      <div className={`
        absolute inset-0 rounded-lg opacity-10
        ${isSelected 
          ? 'bg-gradient-to-br from-green-400 to-green-600' 
          : 'bg-gradient-to-br from-blue-400 to-purple-600'
        }
      `} />

      {/* Content */}
      <div className="relative p-4 space-y-3">
        {/* Title */}
        <h3 className="font-semibold text-gray-800 text-sm leading-tight line-clamp-2">
          {property.title}
        </h3>

        {/* Price and Rating Row */}
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-1">
            <span className="text-lg font-bold text-green-600">{property.price}</span>
          </div>
          
          <div className="flex items-center space-x-1">
            <span className="text-yellow-500">⭐</span>
            <span className="text-sm font-medium text-gray-700">{property.rating}</span>
          </div>
        </div>

        {/* Source */}
        <div className="text-xs text-gray-500 flex items-center space-x-1">
          <span>🏢</span>
          <span>{property.source || 'Airbnb'}</span>
        </div>

        {/* Voice Command Hint */}
        <div className="text-xs text-gray-400 italic">
          Say "Select property {index + 1}" or "Choose {index === 0 ? 'first' : index === 1 ? 'second' : index === 2 ? 'third' : `number ${index + 1}`}"
        </div>

        {/* Selection Overlay */}
        {isSelected && (
          <div className="absolute inset-0 bg-green-500 bg-opacity-20 rounded-lg flex items-center justify-center">
            <div className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium">
              Selected! ✓
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PropertyCard; 