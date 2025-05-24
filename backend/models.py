from pydantic import BaseModel
from typing import List, Dict, Optional

# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str
    status: str
    search_results: Optional[List[Dict]] = None

# Search parameters model
class SearchParams(BaseModel):
    location: Optional[str] = None
    checkin: Optional[str] = None
    checkout: Optional[str] = None
    guests: Optional[int] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    property_type: Optional[str] = None
    amenities: Optional[List[str]] = None

# Airbnb amenity IDs and constants
AIRBNB_AMENITIES = {
    'wifi': 4,
    'kitchen': 8,
    'washer': 33,
    'dryer': 34,
    'air_conditioning': 5,
    'heating': 30,
    'tv': 1,
    'pool': 7,
    'hot_tub': 25,
    'parking': 9,
    'gym': 15,
    'breakfast': 16,
    'pets_allowed': 12,
    'smoking_allowed': 11,
    'elevator': 21,
    'wheelchair_accessible': 65
}

AIRBNB_PROPERTY_TYPES = {
    'house': 1,
    'apartment': 2,
    'bed_and_breakfast': 3,
    'boutique_hotel': 43,
    'bungalow': 7,
    'cabin': 8,
    'chalet': 10,
    'cottage': 11,
    'loft': 17,
    'villa': 32,
    'townhouse': 31
}

AIRBNB_ROOM_TYPES = [
    'Entire home/apt',
    'Private room',
    'Shared room'
] 