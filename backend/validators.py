import re
from models import SearchParams

def validate_and_fix_params(params: SearchParams, conversation_text: str) -> SearchParams:
    """Validate and fix extracted parameters before using them"""
    print(f"DEBUG - Validating parameters: {params}")
    
    # Fix guest count (should be 1-16, not prices)
    if params.guests and params.guests > 16:
        print(f"DEBUG - Invalid guest count {params.guests}, fixing...")
        # Look for more reasonable guest patterns
        guest_patterns = [
            r"(\d+)\s+(?:people|guests?|person|adults?)",
            r"(?:for|with)\s+(\d+)(?:\s+(?:people|guests|adults))",
            r"(\d+)\s+of us"
        ]
        
        new_guests = None
        for pattern in guest_patterns:
            matches = re.finditer(pattern, conversation_text, re.IGNORECASE)
            for match in matches:
                guest_num = int(match.group(1))
                if 1 <= guest_num <= 16:  # Reasonable guest count
                    new_guests = guest_num
                    break
            if new_guests:
                break
        
        params.guests = new_guests or 2  # Default to 2 guests
        print(f"DEBUG - Fixed guest count to: {params.guests}")
    
    # Fix price range (look for $150-200 pattern that was missed)
    if conversation_text:
        # Look for explicit price ranges mentioned, but only if extraction failed
        price_fix_patterns = [
            r"under\s+\$?(\d+)",  # "under $150" - should set max only
            r"below\s+\$?(\d+)",  # "below $150" - should set max only
            r"(\d+)\$?\s*(?:per\s*night\s*)?maximum.*?(\d+)\$?\s*area",  # "200$ maximum...150$ area"
            r"around\s+\$?(\d+)",  # "around $150"
            r"(\d+)\s*(?:to|through|-)\s*(\d+)\s*(?:dollars?|\$|per\s*night)",
            r"budget.*?\$?(\d+)",
            r"max.*?\$?(\d+)",
            r"up\s+to\s+\$?(\d+)"  # "up to $150"
        ]
        
        # Only try to fix if current extraction seems wrong or incomplete
        should_fix_price = (
            (params.max_price and params.max_price > 500) or  # Extracted price too high
            (params.min_price and params.min_price > params.max_price if params.max_price else False) or  # Invalid range
            (not params.max_price and not params.min_price)  # No price extracted
        )
        
        if should_fix_price:
            for pattern in price_fix_patterns:
                match = re.search(pattern, conversation_text, re.IGNORECASE)
                if match:
                    # Check if this is an "under/below/max/up to" pattern
                    pattern_text = match.group(0).lower()
                    is_max_constraint = any(word in pattern_text for word in ["under", "below", "max", "up to"])
                    
                    if match.lastindex == 2:  # Two numbers found
                        num1, num2 = int(match.group(1)), int(match.group(2))
                        if 20 <= num1 <= 1000 and 20 <= num2 <= 1000:  # Reasonable prices
                            params.min_price = min(num1, num2) - 50  # Buffer
                            params.max_price = max(num1, num2)
                            print(f"DEBUG - Fixed price range to: ${params.min_price}-${params.max_price}")
                            break
                    else:  # Single number
                        price = int(match.group(1))
                        if 20 <= price <= 1000:  # Reasonable price
                            if is_max_constraint:
                                params.max_price = price
                                params.min_price = max(20, price - 100)  # Set reasonable minimum
                                print(f"DEBUG - Fixed max price constraint to: ${params.min_price}-${params.max_price}")
                            else:  # Around this price
                                params.max_price = price + 50
                                params.min_price = max(20, price - 50)
                                print(f"DEBUG - Fixed price range around ${price} to: ${params.min_price}-${params.max_price}")
                            break
    
    # Ensure reasonable defaults
    if params.guests is None or params.guests < 1:
        params.guests = 2
    if params.guests > 16:
        params.guests = 16
        
    if params.max_price and params.max_price > 2000:
        params.max_price = 500  # Cap at reasonable amount
        
    if params.min_price and params.min_price < 0:
        params.min_price = 20
        
    print(f"DEBUG - Final validated parameters: location='{params.location}', guests={params.guests}, price=${params.min_price}-${params.max_price}")
    return params

def should_trigger_search(message: str, params: SearchParams, conversation_history: list) -> bool:
    """
    AGGRESSIVE search triggering logic - search immediately when we have sufficient info.
    Don't make users wait or ask multiple times.
    """
    
    # Must have location as absolute minimum
    if not params.location:
        print("DEBUG - No search: Missing location")
        return False
    
    message_lower = message.lower().strip()
    
    # IMMEDIATE SEARCH CONDITIONS - very generous
    
    # 1. Any affirmative response - search immediately
    affirmative_responses = [
        "yes", "yep", "yeah", "ok", "okay", "sure", "go", "go ahead", 
        "do it", "correct", "that's right", "start searching", "search",
        "find", "let's go", "proceed", "continue", "good", "right", "fine",
        "perfect", "exactly", "sounds good", "looks good", "confirmed",
        "do it now", "search now", "start", "begin", "now", "please"
    ]
    
    if message_lower in affirmative_responses:
        print(f"DEBUG - IMMEDIATE SEARCH: Affirmative response '{message_lower}'")
        return True
    
    # 2. Explicit search commands - always search
    explicit_search_triggers = [
        "search", "find", "look for", "show me", "what's available", "available",
        "can you search", "let's see", "search for", "find me", "show options", 
        "what do you have", "let me see", "get me", "just get me", "now search",
        "do search", "start search", "run search", "please search", "search please"
    ]
    
    if any(trigger in message_lower for trigger in explicit_search_triggers):
        print(f"DEBUG - IMMEDIATE SEARCH: Explicit search command detected")
        return True
    
    # 3. Budget/price mentions - if user gives price info, search immediately
    price_indicators = [
        "$", "budget", "max", "maximum", "under", "below", "up to", "around",
        "cost", "price", "expensive", "cheap", "affordable", "dollar"
    ]
    
    if any(indicator in message_lower for indicator in price_indicators):
        print(f"DEBUG - IMMEDIATE SEARCH: Price/budget mentioned")
        return True
    
    # 4. Date mentions - if user gives dates, search immediately
    date_indicators = [
        "june", "july", "august", "may", "april", "march", "january", "february",
        "september", "october", "november", "december", "/", "-", "check in", 
        "check out", "checkin", "checkout", "dates", "when", "stay"
    ]
    
    if any(date in message_lower for date in date_indicators):
        print(f"DEBUG - IMMEDIATE SEARCH: Date mentioned")
        return True
    
    # 5. Guest count mentions - search immediately
    guest_indicators = [
        "people", "guests", "guest", "adults", "adult", "person", "persons",
        "for 1", "for 2", "for 3", "for 4", "for 5", "for 6", "for 7", "for 8",
        "1 person", "2 people", "3 people", "4 people", "5 people", "6 people"
    ]
    
    if any(guest in message_lower for guest in guest_indicators):
        print(f"DEBUG - IMMEDIATE SEARCH: Guest count mentioned")
        return True
    
    # 6. Auto-trigger if we have location + ANY additional parameter - be very aggressive
    has_additional_info = (
        params.guests or 
        params.max_price or 
        params.min_price or 
        params.property_type or
        params.checkin or
        params.checkout or
        (params.amenities and len(params.amenities) > 0)
    )
    
    if params.location and has_additional_info:
        # Only check for explicit "no" or "stop" commands
        stop_words = ["no", "not", "don't", "stop", "wait", "hold on", "first", "before"]
        if not any(stop in message_lower for stop in stop_words):
            print(f"DEBUG - AUTO SEARCH: Have location + additional info (guests={params.guests}, price={params.max_price}, dates={params.checkin})")
            return True
    
    # 7. Area/location specifications - search immediately
    area_specs = [
        "downtown", "center", "near", "close to", "area", "district", 
        "neighborhood", "region", "zone", "part of", "side of"
    ]
    
    if params.location and any(spec in message_lower for spec in area_specs):
        print(f"DEBUG - IMMEDIATE SEARCH: Location + area specification")
        return True
    
    # 8. Property type mentions - search immediately
    property_types = [
        "apartment", "house", "villa", "cabin", "loft", "cottage", "home",
        "studio", "room", "place", "accommodation", "rental"
    ]
    
    if params.location and any(prop_type in message_lower for prop_type in property_types):
        print(f"DEBUG - IMMEDIATE SEARCH: Location + property type mentioned")
        return True
    
    # 9. If user is providing any specific details at all - search
    detail_patterns = [
        r"\d+",  # Any number (guests, dates, prices)
        r"[A-Z][a-z]+\s+\d+",  # Month + day patterns
        r"\d+/\d+",  # Date patterns
        r"\$\d+",  # Price patterns
    ]
    
    if params.location:
        for pattern in detail_patterns:
            if re.search(pattern, message):
                print(f"DEBUG - IMMEDIATE SEARCH: Location + specific details provided")
                return True
    
    # 10. If this message contains a location for the first time - search immediately
    # (Don't make user wait for confirmation)
    if params.location:
        # Check if this is the first time location was mentioned
        previous_messages = " ".join([msg.get("text", "") for msg in conversation_history if msg.get("sender") == "user"])
        if params.location.lower() not in previous_messages.lower():
            print(f"DEBUG - IMMEDIATE SEARCH: New location mentioned - searching immediately")
            return True
    
    print(f"DEBUG - No search triggered for message: '{message}'")
    return False

def should_show_confirmation(params: SearchParams, conversation_history: list) -> bool:
    """
    VERY RESTRICTIVE confirmation logic - almost never show confirmations.
    Just search immediately in 95% of cases.
    """
    
    # Must have location as minimum
    if not params.location:
        return False
    
    # NEVER show confirmation if we already have detailed parameters
    has_good_info = (
        params.location and (
            params.guests or 
            params.max_price or 
            params.min_price or
            params.checkin or
            params.checkout
        )
    )
    
    if has_good_info:
        print("DEBUG - No confirmation: Have sufficient details for immediate search")
        return False
    
    # Check if we recently showed a confirmation - NEVER repeat
    recent_conversation = ""
    if conversation_history:
        for msg in conversation_history[-10:]:  # Check last 10 messages
            if msg.get("sender") == "assistant":
                recent_conversation += msg.get("text", "").lower()
    
    confirmation_indicators = [
        "is this correct", "should i start searching", "would you like me to search",
        "ready to search", "does this look good", "confirm these details",
        "search for", "does this sound right", "correct?", "right?",
        "shall i", "should i", "ready to", "confirmation", "confirm",
        "would you like", "want me to"
    ]
    
    if any(indicator in recent_conversation for indicator in confirmation_indicators):
        print("DEBUG - No confirmation: Already asked recently")
        return False
    
    # Only show confirmation in extremely rare cases - when we ONLY have location
    # and user hasn't given any other details at all
    only_has_location = (
        params.location and
        not params.guests and
        not params.max_price and
        not params.min_price and
        not params.checkin and
        not params.checkout and
        not params.property_type and
        not params.amenities
    )
    
    if only_has_location:
        # Even then, only if the conversation is very short (they just said the city)
        total_user_messages = len([msg for msg in conversation_history if msg.get("sender") == "user"])
        if total_user_messages <= 2:  # Very early in conversation
            print("DEBUG - Showing confirmation: Only location provided early in conversation")
            return True
    
    print("DEBUG - No confirmation: Proceeding directly to search")
    return False

def get_missing_params_message(params: SearchParams) -> str:
    """Generate a helpful message about what information is still needed"""
    missing = []
    
    if not params.location:
        missing.append("destination/location")
    
    if not params.guests:
        missing.append("number of guests")
        
    if not params.min_price and not params.max_price:
        missing.append("budget range")
    
    if missing:
        return f"I still need a few more details: {', '.join(missing)}. "
    
    return "I have most of the information. Would you like me to search for options now?" 