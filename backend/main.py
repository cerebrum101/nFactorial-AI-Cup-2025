from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from groq import Groq
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta

# Import our modular components
from models import ChatMessage, ChatResponse
from extractors import extract_search_params
from validators import validate_and_fix_params, should_trigger_search, should_show_confirmation, get_missing_params_message
from scrapers import scrape_airbnb_listings
from utils import build_airbnb_url, get_persona_prompt, format_search_confirmation

# Load environment variables
load_dotenv()

app = FastAPI(title="Condfind Backend", description="AI Assistant for Airbnb Listings")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000",
        "https://your-frontend-domain.vercel.app",  # Add your Vercel domain
        "*"  # For development only
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.get("/")
async def root():
    return {"message": "Condfind Backend is running!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_data: ChatMessage):
    try:
        # Extract search parameters from USER messages only (not mixed conversation)
        user_messages = [msg["text"] for msg in chat_data.conversation_history if msg["sender"] == "user"]
        user_messages.append(chat_data.message)  # Add current user message
        user_conversation = " ".join(user_messages)
        
        print(f"DEBUG - User messages only: {user_conversation}")
        
        search_params = extract_search_params(user_conversation)
        
        # Validate and fix the extracted parameters
        search_params = validate_and_fix_params(search_params, user_conversation)
        
        # Debug: Print extracted parameters
        print(f"DEBUG - Full conversation: {user_conversation}")
        print(f"DEBUG - Extracted location: {search_params.location}")
        print(f"DEBUG - Extracted guests: {search_params.guests}")
        print(f"DEBUG - Extracted price range: ${search_params.min_price}-${search_params.max_price}")
        
        # NEW: Check if we should show confirmation before searching
        should_confirm = should_show_confirmation(search_params, chat_data.conversation_history)
        should_search = should_trigger_search(
            chat_data.message, 
            search_params, 
            chat_data.conversation_history
        )
        
        print(f"DEBUG - Should show confirmation: {should_confirm}")
        print(f"DEBUG - Should trigger search: {should_search}")
        
        search_results = None
        persona_prompt = get_persona_prompt()
        
        if should_search and search_params.location:
            # User confirmed - proceed with search
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
                
                persona_prompt = get_persona_prompt(search_context)
            except Exception as e:
                print(f"DEBUG - Search error: {e}")
                persona_prompt = get_persona_prompt(f"\n\nNOTE: Search attempted but encountered issues. Acknowledge this and offer to try again or help in other ways.")
        
        elif should_confirm and search_params.location:
            # Show confirmation before searching
            confirmation_message = format_search_confirmation(search_params)
            persona_prompt = get_persona_prompt(f"\n\nCONTEXT: Show this confirmation message to the user: '{confirmation_message}'. Do not search yet - wait for their confirmation.")
        
        else:
            # Add context about missing information
            missing_info = get_missing_params_message(search_params)
            persona_prompt = get_persona_prompt(f"\n\nCONTEXT: {missing_info}")
        
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

@app.post("/choose-property")
async def choose_property(request_data: dict):
    """
    Handle property selection and generate booking/messaging URLs
    """
    try:
        property_data = request_data.get('property')
        search_params = request_data.get('search_params', {})
        
        if not property_data:
            raise HTTPException(status_code=400, detail="Property data is required")
        
        # Extract property details
        property_title = property_data.get('title', '')
        property_url = property_data.get('link', '')
        property_price = property_data.get('price', '')
        property_rating = property_data.get('rating', '')
        
        # Generate URLs for messaging and booking
        urls = generate_airbnb_urls(property_url, search_params)
        
        # Create confirmation message
        confirmation_message = f"""🎉 Perfect choice! You've selected:

**{property_title}**
💰 {property_price} • ⭐ {property_rating}

I've prepared two options for you:

1. **Message Host** - Ask questions about amenities, check-in process, local area, etc.
2. **Book Now** - Proceed directly to complete your reservation

Both options will redirect you to Airbnb.com for secure transactions and direct communication with the host.

What would you like to do next?"""
        
        return {
            "message": confirmation_message,
            "selected_property": property_data,
            "urls": urls,
            "next_steps": ["message_host", "book_now"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process property choice: {str(e)}")

def generate_airbnb_urls(listing_url, search_params=None):
    """
    Generate message host and booking URLs from a listing URL
    """
    if search_params is None:
        search_params = {}
    
    # Extract room ID from URL
    room_id = extract_room_id(listing_url)
    
    if not room_id:
        # Fallback to original URL
        return {
            "message_host_url": listing_url,
            "booking_url": listing_url,
            "room_id": None
        }
    
    # Generate message host URL with proper format
    guests = search_params.get('guests', 2)
    
    # Build contact host URL parameters
    contact_params = [f"adults={guests}"]
    
    # Add dates if available (use underscore format for contact host)
    if search_params.get('check_in'):
        contact_params.append(f"check_in={search_params['check_in']}")
    if search_params.get('check_out'):
        contact_params.append(f"check_out={search_params['check_out']}")
    else:
        # Add default dates
        check_in = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        check_out = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        contact_params.extend([f"check_in={check_in}", f"check_out={check_out}"])
    
    contact_query = "&".join(contact_params)
    message_host_url = f"https://www.airbnb.com/contact_host/{room_id}/send_message?{contact_query}"
    
    # Generate booking URL with proper format
    booking_url = generate_booking_url(room_id, search_params)
    
    return {
        "message_host_url": message_host_url,
        "booking_url": booking_url,
        "room_id": room_id
    }

def extract_room_id(airbnb_url):
    """
    Extract room ID from various Airbnb URL formats
    """
    try:
        patterns = [
            r'/rooms/(\d+)',  # Standard format
            r'listing_(\d+)',  # Alternative format
            r'/(\d+)\?',  # Room ID before query params
        ]
        
        for pattern in patterns:
            match = re.search(pattern, airbnb_url)
            if match:
                return match.group(1)
        
        return None
    except Exception:
        return None

def generate_booking_url(room_id, search_params):
    """
    Generate booking URL with search parameters using working format
    """
    guests = search_params.get('guests', 2)
    
    # Build query parameters using the exact working format
    params = [
        f"numberOfAdults={guests}",
        f"guestCurrency=USD",
        f"productId={room_id}",
        f"isWorkTrip=false",
        f"numberOfChildren=0",
        f"numberOfGuests={guests}",
        f"numberOfInfants=0",
        f"numberOfPets=0"
    ]
    
    # Add dates if available (no underscore format for booking)
    if search_params.get('check_in'):
        params.append(f"checkin={search_params['check_in']}")
    if search_params.get('check_out'):
        params.append(f"checkout={search_params['check_out']}")
    else:
        # Add default dates
        check_in = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        check_out = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        params.extend([f"checkin={check_in}", f"checkout={check_out}"])
    
    query_string = "&".join(params)
    
    # Use the exact working format
    return f"https://www.airbnb.com/book/stays/{room_id}?{query_string}"

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "condfind-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 