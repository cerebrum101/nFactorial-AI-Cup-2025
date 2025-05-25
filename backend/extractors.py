import re
import json
import os
from typing import List
from models import SearchParams, AIRBNB_PROPERTY_TYPES
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client for parameter extraction

def get_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))



def extract_search_params_with_llm(conversation_text: str) -> SearchParams:
    """Use LLM to extract search parameters from conversation in any language"""
    
    extraction_prompt = f"""
Extract travel accommodation search parameters from this conversation. The user might be speaking in any language (English, Russian, Spanish, etc.).

Conversation: "{conversation_text}"

Please extract and respond with ONLY a JSON object in this exact format:
{{
    "location": "city name in English (e.g. Istanbul, New York, Moscow)",
    "guests": number or null,
    "min_price": number or null, 
    "max_price": number or null,
    "property_type": "apartment/house/villa/cabin/loft/cottage" or null
}}

CRITICAL PRICING RULES:
- "70 USD max" or "maximum 70" or "up to 70" → set ONLY max_price: 70, min_price: null
- "under 150" or "below 150" → set ONLY max_price: 150, min_price: null  
- "around 200" or "about 200" or "roughly 200" → set min_price: 150, max_price: 250
- "100-200" or "between 100 and 200" or "from 100 to 200" → set min_price: 100, max_price: 200
- "at least 100" or "minimum 100" or "starting from 100" → set ONLY min_price: 100, max_price: null

EXAMPLES:
- "70 per day max" → {"min_price": null, "max_price": 70}
- "around 200 per night" → {"min_price": 150, "max_price": 250}  
- "100 to 300 range" → {"min_price": 100, "max_price": 300}
- "under 80 dollars" → {"min_price": null, "max_price": 80}

OTHER RULES:
- Convert city names to English (стамбул → Istanbul, нью-йорк → New York)
- Extract guest count from phrases like "4 adults", "нас 4", "2 people"
- For property types: flat/apartment → "apartment", house/home → "house"
- Return null for missing information

DO NOT set both min_price and max_price to the same value unless explicitly given a range!
"""

    try:
        print(f"DEBUG - LLM extraction input: '{conversation_text[:200]}...'")
        
        completion = get_groq_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=200
        )
        
        response_text = completion.choices[0].message.content.strip()
        print(f"DEBUG - LLM extraction response: {response_text}")
        
        # Parse the JSON response
        try:
            extracted_data = json.loads(response_text)
            
            params = SearchParams()
            params.location = extracted_data.get('location')
            params.guests = extracted_data.get('guests')
            params.min_price = extracted_data.get('min_price') 
            params.max_price = extracted_data.get('max_price')
            params.property_type = extracted_data.get('property_type')
            
            print(f"DEBUG - LLM extracted successfully: location='{params.location}', guests={params.guests}, price=${params.min_price}-${params.max_price}")
            return params
            
        except json.JSONDecodeError as e:
            print(f"DEBUG - JSON parsing error: {e}")
            print(f"DEBUG - Raw LLM response: '{response_text}'")
            # Fallback to regex extraction
            return extract_search_params_regex(conversation_text)
            
    except Exception as e:
        print(f"DEBUG - LLM extraction error: {e}")
        print(f"DEBUG - Falling back to regex extraction")
        # Fallback to regex extraction
        return extract_search_params_regex(conversation_text)

def extract_search_params_regex(conversation_text: str) -> SearchParams:
    """Extract search parameters from conversation using regex patterns"""
    params = SearchParams()
    
    print(f"DEBUG - Input text: '{conversation_text}'")
    
    # First try to find known cities/locations directly (more reliable)
    known_locations = [
        'almaty', 'astana', 'shymkent', 'aktobe', 'taraz', 'pavlodar',
        'tokyo', 'new york', 'london', 'paris', 'berlin', 'madrid', 'rome',
        'moscow', 'beijing', 'seoul', 'bangkok', 'dubai', 'istanbul', 'kazakhstan',
        # Russian/Cyrillic names
        'стамбул', 'москва', 'алматы', 'астана', 'токио', 'лондон', 'париж',
        
    ]
    
    
    
    # Check for known locations first (highest priority)
    for known in known_locations:
        # Use word boundaries to match exact city names
        pattern = r'\b' + re.escape(known.lower()) + r'\b'
        if re.search(pattern, conversation_text.lower()):
            params.location = known.title()
            print(f"DEBUG - Found known location: '{params.location}'")
            break
    
    # If no known location found, try pattern matching
    if not params.location:
        # More specific location patterns
        location_patterns = [
            # Specific travel prepositions with city names
            r"(?:in|to|at|visit|stay in|going to|traveling to|fly to|book in|rent.*in)\s+([A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]+)*?)(?:\s+in\s+\d|\s+for\s+\d|\s+with\s+\d|\s*[,.]|\s*$)",
            # Looking for places/areas
            r"(?:place|area|city|town)\s+(?:like|in|near)\s+([A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]+)*)",
        ]
        
        for i, pattern in enumerate(location_patterns):
            matches = re.finditer(pattern, conversation_text, re.IGNORECASE)
            for match in matches:
                if not params.location:
                    location = match.group(1).strip()
                    print(f"DEBUG - Pattern {i+1} found potential location: '{location}'")
                    
                    # Strict filtering of non-locations
                    non_locations = {
                        'help', 'looking', 'need', 'want', 'find', 'search', 'book', 'stay', 
                        'apartment', 'house', 'place', 'room', 'home', 'hotel', 'rental',
                        'cheap', 'expensive', 'budget', 'luxury', 'nice', 'good', 'great', 'perfect',
                        'people', 'guests', 'adults', 'person', 'me', 'us', 'them',
                        'night', 'day', 'week', 'month', 'year', 'time', 'date',
                        'price', 'cost', 'money', 'dollar', 'budget', 'accommodation',
                        'something', 'somewhere', 'anywhere', 'anything', 'everything',
                        'you', 'find', 'the', 'perfect', 'airbnb', 'help you find',
                        'mountains', 'beach', 'downtown', 'center', 'close', 'closer', 'near'  # Geographic descriptors, not cities
                    }
                    
                    # Clean the location and check if it's valid
                    location_clean = location.strip().lower()
                    location_words = location_clean.split()
                    
                    # Check if any word in the location is a non-location
                    is_valid_location = True
                    for word in location_words:
                        if word in non_locations:
                            is_valid_location = False
                            print(f"DEBUG - Rejected '{location}' because it contains non-location word: '{word}'")
                            break
                    
                    # Additional checks for valid locations
                    if (is_valid_location and 
                        len(location_clean) > 2 and 
                        location_clean not in non_locations and
                        not any(phrase in location_clean for phrase in ['help you', 'find the', 'perfect airbnb'])):
                        
                        # Capitalize properly for URL
                        params.location = location.title()
                        print(f"DEBUG - Accepted location: '{params.location}'")
                        break
                    else:
                        print(f"DEBUG - Rejected location: '{location}' (failed validation)")
    
    # Guest count patterns
    guest_patterns = [
        r"(\d+)\s+(?:people|guests?|person|adults?)",
        r"(?:for|with)\s+(\d+)",
        r"(\d+)\s+of us"
    ]
    
    for pattern in guest_patterns:
        match = re.search(pattern, conversation_text, re.IGNORECASE)
        if match and not params.guests:
            params.guests = int(match.group(1))
            break
    
    # Budget patterns - improved to handle "70 USD max" properly
    budget_patterns = [
        r"(\d+)\s*(?:usd|USD|dollars?)\s*(?:max|maximum|per\s*day\s*max)",  # "70 USD max", "70 dollars max"
        r"(\d+)\s*(?:per\s*day|daily|nightly?)\s*(?:max|maximum)",  # "70 per day max"
        r"max(?:imum)?\s*(?:of\s*)?(?:usd\s*)?(?:\$)?(\d+)",  # "maximum $70", "max of 70"
        r"under\s*(?:\$)?(\d+)",  # "under $70"
        r"below\s*(?:\$)?(\d+)",  # "below 70"
        r"up\s*to\s*(?:\$)?(\d+)",  # "up to 70"
        r"(\d+)\s*(?:kzt|tenge)",  # KZT currency
        r"\$(\d+)(?:\s*-\s*\$?(\d+))?",  # $70-100 or $70
        r"(\d+)\s*(?:to|through|-)\s*(\d+)\s*(?:dollars?|\$)",  # 70 to 100 dollars
        r"budget\s+(?:of\s+)?(?:around\s+)?\$?(\d+)",  # budget of $70
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, conversation_text, re.IGNORECASE)
        if match and not params.min_price and not params.max_price:
            print(f"DEBUG - Budget pattern matched: '{match.group(0)}'")
            
            if 'kzt' in pattern.lower() or 'tenge' in pattern.lower():
                # Convert KZT to USD (rough approximation: 1 USD = 450 KZT)
                kzt_amount = int(match.group(1))
                usd_amount = kzt_amount // 450
                params.max_price = usd_amount
                print(f"DEBUG - Converted {kzt_amount} KZT to ~${usd_amount} USD")
            elif match.lastindex >= 2 and match.group(2):  # Range found (two numbers)
                params.min_price = int(match.group(1))
                params.max_price = int(match.group(2))
                print(f"DEBUG - Price range extracted: ${params.min_price}-${params.max_price}")
            else:  # Single price found
                price = int(match.group(1))
                pattern_text = match.group(0).lower()
                
                # Check if this is a maximum constraint
                if any(word in pattern_text for word in ["max", "under", "below", "up to"]):
                    params.max_price = price
                    print(f"DEBUG - Maximum price extracted: ${params.max_price}")
                else:
                    # Budget around this price
                    params.min_price = max(20, price - 30)
                    params.max_price = price + 30
                    print(f"DEBUG - Budget around ${price} extracted: ${params.min_price}-${params.max_price}")
            break
    
    # Property type patterns
    property_patterns = [
        r"\b(house|houses|home|homes)\b",
        r"\b(apartment|apartments|apt|apts)\b",
        r"\b(villa|villas)\b",
        r"\b(cabin|cabins)\b",
        r"\b(loft|lofts)\b",
        r"\b(cottage|cottages)\b"
    ]
    
    property_mapping = {
        'house': 'house', 'houses': 'house', 'home': 'house', 'homes': 'house',
        'apartment': 'apartment', 'apartments': 'apartment', 'apt': 'apartment', 'apts': 'apartment',
        'villa': 'villa', 'villas': 'villa',
        'cabin': 'cabin', 'cabins': 'cabin',
        'loft': 'loft', 'lofts': 'loft',
        'cottage': 'cottage', 'cottages': 'cottage'
    }
    
    for pattern in property_patterns:
        match = re.search(pattern, conversation_text, re.IGNORECASE)
        if match and not params.property_type:
            matched_type = match.group(1).lower()
            if matched_type in property_mapping:
                params.property_type = property_mapping[matched_type]
                break
    
    # Amenity patterns
    amenity_patterns = {
        'wifi': r'\b(wifi|wi-fi|internet|wireless)\b',
        'kitchen': r'\b(kitchen|cook|cooking|kitchenette)\b',
        'pool': r'\b(pool|swimming|swim)\b',
        'parking': r'\b(parking|garage|park)\b',
        'air_conditioning': r'\b(air\s*conditioning|ac|a/c|cool|cooling)\b',
        'washer': r'\b(washer|washing|laundry)\b',
        'hot_tub': r'\b(hot\s*tub|jacuzzi|spa)\b',
        'gym': r'\b(gym|fitness|workout)\b',
        'pets_allowed': r'\b(pet|pets|dog|cat|pet-friendly)\b'
    }
    
    detected_amenities = []
    for amenity, pattern in amenity_patterns.items():
        if re.search(pattern, conversation_text, re.IGNORECASE):
            detected_amenities.append(amenity)
    
    if detected_amenities:
        params.amenities = detected_amenities
    
    print(f"DEBUG - Final extracted params: location='{params.location}', guests={params.guests}, price_max={params.max_price}, property_type='{params.property_type}'")
    
    return params 

def extract_search_params(conversation_text: str) -> SearchParams:
    """Extract search parameters from conversation text - optimized for speed"""
    
    # Try fast regex extraction first
    params = extract_search_params_regex(conversation_text)
    
    # Only use expensive LLM if we have complex input and missing critical info
    needs_llm = (
        not params.location and  # No location found
        len(conversation_text) > 50 and  # Complex enough to warrant LLM
        any(keyword in conversation_text.lower() for keyword in [
            'accommodation', 'travel', 'trip', 'visit', 'booking', 'stay'
        ])
    )
    
    if needs_llm:
        print("DEBUG - Using LLM for complex parameter extraction")
        llm_params = extract_search_params_with_llm(conversation_text)
        # Merge results - prioritize LLM location if regex failed
        if llm_params.location and not params.location:
            params.location = llm_params.location
        if llm_params.guests and not params.guests:
            params.guests = llm_params.guests
        if llm_params.min_price and not params.min_price:
            params.min_price = llm_params.min_price
        if llm_params.max_price and not params.max_price:
            params.max_price = llm_params.max_price
    else:
        print("DEBUG - Using fast regex extraction only")
    
    return params 