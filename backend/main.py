from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import re
import json
import urllib.parse
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = FastAPI(title="Condfind Backend", description="AI Assistant for Airbnb Listings")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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

def extract_search_params(conversation_text: str) -> SearchParams:
    """Extract search parameters from conversation using regex patterns"""
    params = SearchParams()
    
    print(f"DEBUG - Input text: '{conversation_text}'")
    
    # First try to find known cities/locations directly (more reliable)
    known_locations = [
        'almaty', 'astana', 'nur-sultan', 'shymkent', 'aktobe', 'taraz', 'pavlodar',
        'tokyo', 'new york', 'london', 'paris', 'berlin', 'madrid', 'rome',
        'moscow', 'beijing', 'seoul', 'bangkok', 'dubai', 'istanbul', 'kazakhstan'
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
    
    # Budget patterns - add KZT support
    budget_patterns = [
        r"(\d+)\s*(?:kzt|tenge)",  # KZT currency
        r"\$(\d+)(?:\s*-\s*\$?(\d+))?",
        r"(\d+)\s*(?:to|through|-)\s*(\d+)\s*(?:dollars?|\$)",
        r"budget\s+(?:of\s+)?(?:around\s+)?\$?(\d+)",
        r"under\s+\$?(\d+)",
        r"max\s+\$?(\d+)"
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, conversation_text, re.IGNORECASE)
        if match and not params.min_price:
            if 'kzt' in pattern.lower() or 'tenge' in pattern.lower():
                # Convert KZT to USD (rough approximation: 1 USD = 450 KZT)
                kzt_amount = int(match.group(1))
                usd_amount = kzt_amount // 450
                params.max_price = usd_amount
                print(f"DEBUG - Converted {kzt_amount} KZT to ~${usd_amount} USD")
            elif match.group(2):  # Range found
                params.min_price = int(match.group(1))
                params.max_price = int(match.group(2))
            else:  # Single price found
                price = int(match.group(1))
                if "under" in match.group(0).lower() or "max" in match.group(0).lower():
                    params.max_price = price
                else:
                    params.min_price = price // 2
                    params.max_price = price * 2
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

def build_airbnb_url(params: SearchParams) -> str:
    """Build Airbnb search URL with proper query parameters"""
    if not params.location:
        return "https://www.airbnb.com/s/homes"
    
    # Clean location for URL
    location_clean = urllib.parse.quote_plus(params.location)
    base_url = f"https://www.airbnb.com/s/{location_clean}/homes"
    
    query_params = []
    
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
    
    # Add price range
    if params.min_price:
        query_params.append(f"price_min={params.min_price}")
    if params.max_price:
        query_params.append(f"price_max={params.max_price}")
    
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

def scrape_airbnb_listings(search_url: str, max_listings: int = 3) -> List[Dict]:
    """Scrape Airbnb search results"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        print(f"DEBUG - Attempting to scrape: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"DEBUG - Response status code: {response.status_code}")
        print(f"DEBUG - Response headers: {dict(response.headers)}")
        print(f"DEBUG - Response content length: {len(response.content)}")
        print(f"DEBUG - First 500 chars of response: {response.text[:500]}")
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        listings = []
        
        # Look for listing containers (Airbnb structure changes frequently)
        potential_selectors = [
            '[data-testid="listing-card-title"]',
            '[data-testid="card-container"]',
            '.c4mnd7m',  # Common Airbnb class
            '[aria-label*="listing"]'
        ]
        
        print(f"DEBUG - Trying {len(potential_selectors)} different selectors...")
        
        for i, selector in enumerate(potential_selectors):
            elements = soup.select(selector)
            print(f"DEBUG - Selector {i+1} '{selector}' found {len(elements)} elements")
            if elements:
                for j, element in enumerate(elements[:max_listings]):
                    try:
                        # Extract basic info
                        title_elem = element.find('div', {'data-testid': 'listing-card-title'}) or element
                        title = title_elem.get_text(strip=True) if title_elem else f"Listing {j+1}"
                        
                        # Try to find price
                        price_elem = element.find_next(string=re.compile(r'\$\d+'))
                        price = price_elem.strip() if price_elem else "Price available on site"
                        
                        # Try to find link
                        link_elem = element.find_parent('a') or element.find('a')
                        link = ""
                        if link_elem and link_elem.get('href'):
                            href = link_elem.get('href')
                            if href.startswith('/'):
                                link = f"https://www.airbnb.com{href}"
                            else:
                                link = href
                        
                        # Try to find rating
                        rating_elem = element.find(string=re.compile(r'\d+\.\d+')) or element.find_next(string=re.compile(r'\d+\.\d+'))
                        rating = rating_elem.strip() if rating_elem else "Rating not available"
                        
                        print(f"DEBUG - Found listing {j+1}: title='{title}', price='{price}', rating='{rating}'")
                        
                        listings.append({
                            'title': title,
                            'price': price,
                            'rating': rating,
                            'link': link,
                            'source': 'airbnb'
                        })
                    except Exception as e:
                        print(f"DEBUG - Error extracting listing {j+1}: {e}")
                        continue
                
                if listings:
                    print(f"DEBUG - Successfully scraped {len(listings)} listings with selector '{selector}'")
                    break
        
        # Check if we found any real listings
        if not listings:
            print("DEBUG - No listings found through scraping, using fallback data")
            # Instead of fake listings, let's provide a clear message
            listings = [
                {
                    'title': f'Real listings available on Airbnb',
                    'price': 'Visit site for current pricing',
                    'rating': 'See reviews on Airbnb',
                    'link': search_url,
                    'source': 'airbnb_redirect'
                }
            ]
        else:
            print(f"DEBUG - Returning {len(listings)} real scraped listings")
        
        return listings[:max_listings]
        
    except Exception as e:
        print(f"DEBUG - Scraping error: {e}")
        # Instead of fake data, return a redirect message
        return [
            {
                'title': f'Properties available in {search_url.split("/s/")[1].split("/")[0] if "/s/" in search_url else "your location"}',
                'price': 'Visit Airbnb for current pricing',
                'rating': 'See actual reviews on site',
                'link': search_url,
                'source': 'airbnb_redirect'
            }
        ]

def should_trigger_search(conversation_text: str, params: SearchParams) -> bool:
    """Determine if we have enough info to trigger a search"""
    # Must have location
    if not params.location:
        return False
    
    # Look for search trigger phrases
    trigger_phrases = [
        "search", "find", "look for", "show me", "what's available",
        "can you search", "let's see", "ready to search"
    ]
    
    conversation_lower = conversation_text.lower()
    has_trigger = any(phrase in conversation_lower for phrase in trigger_phrases)
    
    # Also trigger if we have location + (guests or budget)
    has_sufficient_info = params.location and (params.guests or params.min_price or params.max_price)
    
    return has_trigger or has_sufficient_info

# Enhanced persona prompt
ENHANCED_PERSONA_PROMPT = """You are Alex, a professional travel agent specializing in Airbnb accommodations for Condfind.

Your personality:
- Friendly but professional
- Detail-oriented and thorough  
- Genuinely excited about helping people find perfect stays
- Ask clarifying questions to understand needs better

Your process:
1. Gather basic info: location, dates, group size, budget
2. When you have enough information (especially location), offer to search
3. Present search results professionally with recommendations

ABSOLUTE CRITICAL RULES - FOLLOW THESE EXACTLY:
- NEVER EVER create, invent, fabricate, or mention ANY specific properties, property names, prices, or ratings that are not provided in the system search results
- NEVER make up property names like "Mountain View House" or "Almaty Hills Retreat"
- NEVER create fake prices in any currency (USD, KZT, EUR, etc.)
- NEVER create fake ratings or review counts
- DO NOT describe specific properties with made-up details

WHEN SEARCH RESULTS ARE PROVIDED BY THE SYSTEM:
- Simply acknowledge: "I found some options for you in [location]" 
- Do NOT describe the individual listings in detail
- Do NOT repeat or paraphrase the search results
- Let the system display the actual results completely
- After results are shown, provide general guidance like "What do you think of these options?" or "Would you like me to search with different criteria?"

WHEN NO SEARCH RESULTS ARE PROVIDED:
- Focus on gathering information needed for an effective search
- Ask about missing details like specific location, budget range, travel dates, or preferences
- Suggest what information would help you find better options

Keep responses conversational but never create fictional property data. You are a search facilitator, not a property inventor."""

@app.get("/")
async def root():
    return {"message": "Condfind Backend is running!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_data: ChatMessage):
    try:
        # Extract search parameters from entire conversation
        full_conversation = " ".join([msg["text"] for msg in chat_data.conversation_history + [{"text": chat_data.message, "sender": "user"}]])
        search_params = extract_search_params(full_conversation)
        
        # Debug: Print extracted parameters
        print(f"DEBUG - Full conversation: {full_conversation}")
        print(f"DEBUG - Extracted location: {search_params.location}")
        print(f"DEBUG - Extracted guests: {search_params.guests}")
        print(f"DEBUG - Extracted price range: ${search_params.min_price}-${search_params.max_price}")
        
        # Check if we should trigger a search
        should_search = should_trigger_search(chat_data.message.lower(), search_params)
        print(f"DEBUG - Should trigger search: {should_search}")
        
        search_results = None
        if should_search and search_params.location:
            try:
                # Build search URL and scrape results
                search_url = build_airbnb_url(search_params)
                print(f"DEBUG - Generated URL: {search_url}")
                search_results = scrape_airbnb_listings(search_url)
                
                # Create enhanced prompt with search context
                search_context = f"\n\nSEARCH RESULTS CONTEXT: You just performed a search for {search_params.location}"
                if search_params.guests:
                    search_context += f" for {search_params.guests} guests"
                if search_params.min_price or search_params.max_price:
                    search_context += f" with budget ${search_params.min_price or 0}-${search_params.max_price or '∞'}"
                
                search_context += f"\n\nFound {len(search_results)} listings. Present them professionally and ask if they'd like more details about any specific property or want to refine the search."
                
                persona_prompt = ENHANCED_PERSONA_PROMPT + search_context
            except Exception as e:
                print(f"DEBUG - Search error: {e}")
                persona_prompt = ENHANCED_PERSONA_PROMPT + f"\n\nNOTE: Search attempted but encountered issues. Acknowledge this and offer to try again or help in other ways."
        else:
            persona_prompt = ENHANCED_PERSONA_PROMPT
        
        # Build conversation history for context
        messages = [{"role": "system", "content": persona_prompt}]
        
        # Add conversation history
        for msg in chat_data.conversation_history:
            messages.append({
                "role": "user" if msg["sender"] == "user" else "assistant",
                "content": msg["text"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": chat_data.message})
        
        # Call Groq API
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
            max_tokens=400,  # Increased for search results
            top_p=1,
            stream=False
        )
        
        response_text = completion.choices[0].message.content
        
        return ChatResponse(
            response=response_text,
            status="success",
            search_results=search_results
        )
        
    except Exception as e:
        print(f"DEBUG - Main error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "condfind-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 