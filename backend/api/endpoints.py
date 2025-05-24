from flask import Flask, request, jsonify
from conversation_handler import ConversationHandler
from search_handler import SearchHandler
import json
import re
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
conversation_handler = ConversationHandler()
search_handler = SearchHandler()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Backend is running!"})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Process conversation
        response = conversation_handler.process_message(message)
        
        # Check if this is a search query
        if conversation_handler.should_search(message):
            try:
                search_results = search_handler.search_airbnb(message)
                response['search_results'] = search_results
                response['show_property_selection'] = True
            except Exception as search_error:
                print(f"Search error: {search_error}")
                response['search_error'] = str(search_error)
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/choose-property', methods=['POST'])
def choose_property():
    """
    Handle property selection and generate booking/messaging URLs
    """
    try:
        data = request.get_json()
        property_data = data.get('property')
        search_params = data.get('search_params', {})
        
        if not property_data:
            return jsonify({"error": "Property data is required"}), 400
        
        # Extract property details
        property_title = property_data.get('title', '')
        property_url = property_data.get('link', '')
        property_price = property_data.get('price', '')
        property_rating = property_data.get('rating', '')
        
        # Generate URLs for messaging and booking
        urls = generate_airbnb_urls(property_url, search_params)
        
        # Create confirmation message
        confirmation_message = f"""
🎉 Perfect choice! You've selected:

**{property_title}**
💰 {property_price} • ⭐ {property_rating}

I've prepared two options for you:

1. **Message Host** - Ask questions about amenities, check-in process, local area, etc.
2. **Book Now** - Proceed directly to complete your reservation

Both options will redirect you to Airbnb.com for secure transactions and direct communication with the host.

What would you like to do next?
        """.strip()
        
        return jsonify({
            "message": confirmation_message,
            "selected_property": property_data,
            "urls": urls,
            "next_steps": ["message_host", "book_now"]
        })
    
    except Exception as e:
        return jsonify({"error": f"Failed to process property choice: {str(e)}"}), 500

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
    
    # Generate message host URL
    message_host_url = f"https://www.airbnb.com/contact_host?listing_id={room_id}"
    
    # Generate booking URL with search parameters
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
    Generate booking URL with search parameters
    """
    guests = search_params.get('guests', 2)
    check_in = search_params.get('check_in')
    check_out = search_params.get('check_out')
    
    # Build query parameters
    params = []
    params.append(f"adults={guests}")
    
    # Add dates if available
    if check_in:
        params.append(f"check_in={check_in}")
    if check_out:
        params.append(f"check_out={check_out}")
    
    # If no dates provided, suggest next week for 3 nights
    if not check_in or not check_out:
        from datetime import datetime, timedelta
        next_week = datetime.now() + timedelta(days=7)
        checkout_date = next_week + timedelta(days=3)
        
        params.append(f"check_in={next_week.strftime('%Y-%m-%d')}")
        params.append(f"check_out={checkout_date.strftime('%Y-%m-%d')}")
    
    query_string = "&".join(params)
    
    # Try different booking URL formats
    booking_urls = [
        f"https://www.airbnb.com/book/stays/{room_id}?{query_string}",
        f"https://www.airbnb.com/rooms/{room_id}/book?{query_string}",
        f"https://www.airbnb.com/rooms/{room_id}?{query_string}",
    ]
    
    return booking_urls[0]  # Return primary format

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 