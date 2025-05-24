import urllib.parse
from datetime import datetime, timedelta
from models import SearchParams, AIRBNB_AMENITIES, AIRBNB_PROPERTY_TYPES, AIRBNB_ROOM_TYPES

def build_airbnb_url(params: SearchParams) -> str:
    """Build Airbnb search URL with proper query parameters"""
    if not params.location:
        return "https://www.airbnb.com/s/homes"
    
    # Clean location for URL
    location_clean = urllib.parse.quote_plus(params.location)
    base_url = f"https://www.airbnb.com/s/{location_clean}/homes"
    
    query_params = []
    
    # Force USD currency to prevent local currency conversion
    query_params.append("currency=USD")
    
    # Add guests
    if params.guests:
        query_params.append(f"adults={params.guests}")
    
    # Add dates (use proper format)
    if params.checkin and params.checkout:
        query_params.extend([
            f"checkin={params.checkin}",
            f"checkout={params.checkout}"
        ])
    else:
        # Add default dates (next week for 3 nights)
        checkin_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        query_params.extend([
            f"checkin={checkin_date}",
            f"checkout={checkout_date}"
        ])
    
    # Add price range (now in USD)
    if params.min_price:
        query_params.append(f"price_min={params.min_price}")
    if params.max_price:
        query_params.append(f"price_max={params.max_price}")
    
    print(f"DEBUG - Price params: min={params.min_price}, max={params.max_price}")
    print(f"DEBUG - URL will have: {[p for p in query_params if 'price' in p]}")
    
    # Add property type using proper Airbnb format
    if params.property_type and params.property_type.lower() in AIRBNB_PROPERTY_TYPES:
        property_id = AIRBNB_PROPERTY_TYPES[params.property_type.lower()]
        query_params.append(f"property_type_id%5B0%5D={property_id}")
    
    # Add room type (default to entire home)
    query_params.append("room_types%5B%5D=Entire%20home%2Fapt")
    
    # Add popular amenities if mentioned
    if params.amenities:
        for amenity in params.amenities:
            if amenity.lower() in AIRBNB_AMENITIES:
                amenity_id = AIRBNB_AMENITIES[amenity.lower()]
                query_params.append(f"amenities%5B{amenity_id}%5D={amenity_id}")
    
    # Add some default popular amenities to improve results
    default_amenities = ['wifi', 'kitchen']
    for amenity in default_amenities:
        if not params.amenities or amenity not in [a.lower() for a in params.amenities]:
            amenity_id = AIRBNB_AMENITIES[amenity]
            query_params.append(f"amenities%5B{amenity_id}%5D={amenity_id}")
    
    if query_params:
        return f"{base_url}?{'&'.join(query_params)}"
    
    return base_url

def format_search_confirmation(params: SearchParams) -> str:
    """Format extracted parameters into a short confirmation message"""
    
    parts = []
    
    # Build short summary
    if params.location:
        parts.append(f"📍 {params.location}")
    
    if params.guests:
        parts.append(f"👥 {params.guests} guests")
    
    if params.max_price:
        parts.append(f"💰 Up to ${params.max_price}/night")
    elif params.min_price:
        parts.append(f"💰 From ${params.min_price}/night")
    
    if params.property_type:
        parts.append(f"🏠 {params.property_type.title()}")
    
    # Create short confirmation
    summary = " • ".join(parts)
    return f"Searching for: {summary}\n\nSound good?"

def get_persona_prompt(search_context: str = "") -> str:
    """Get the concise persona prompt with optional search context"""
    base_prompt = """You are Alex, a helpful AI travel assistant for Condfind. Be friendly but CONCISE and DIRECT.

Your job:
1. Help find Airbnb properties  
2. Extract search details (location, guests, budget, dates)
3. When you have location + basic details, search immediately
4. Present results clearly

CRITICAL RULES:
- Be brief and to the point
- Don't over-explain or ask multiple confirmations  
- NEVER create fake property names, prices, or ratings
- Only mention properties from actual search results
- When search results are provided, just say "I found some options!" and let the system show them

WHEN YOU HAVE ENOUGH INFO (location + any details):
- Just search immediately, don't ask for confirmation
- Say something brief like "Searching [location] for you..." then search

Keep responses short and actionable."""
    
    return base_prompt + search_context 