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
    Balanced search triggering logic - confirm comprehensive details, auto-search simple responses.
    """
    
    # Must have location as absolute minimum
    if not params.location:
        print("DEBUG - No search: Missing location")
        return False
    
    message_lower = message.lower().strip()
    
    # 1. Simple affirmative responses to confirmations - ALWAYS search
    simple_affirmative = [
        "yes", "yep", "yeah", "ok", "okay", "sure", "go", "go ahead", 
        "do it", "correct", "that's right", "search", "find", "start",
        "perfect", "exactly", "sounds good", "looks good", "confirmed"
    ]
    
    if message_lower in simple_affirmative:
        print(f"DEBUG - IMMEDIATE SEARCH: Affirmative response '{message_lower}'")
        return True
    
    # 2. Explicit search commands with "now", "please", etc. - search immediately
    urgent_search_triggers = [
        "search now", "find now", "go ahead and search", "search please",
        "just search", "start search", "run search", "do search"
    ]
    
    if any(trigger in message_lower for trigger in urgent_search_triggers):
        print(f"DEBUG - IMMEDIATE SEARCH: Urgent search command detected")
        return True
    
    # 3. If message ends with explicit search triggers like "go", "search" - search immediately
    message_words = message_lower.split()
    last_word = message_words[-1] if message_words else ""
    
    if last_word in ["go", "search", "find", "now", "please"]:
        print(f"DEBUG - IMMEDIATE SEARCH: Message ends with search trigger '{last_word}'")
        return True
    
    # 4. If this is a follow-up message after we already have good info - don't auto-search
    # This prevents the comprehensive details issue
    has_comprehensive_info = (
        params.location and
        params.guests and
        (params.max_price or params.min_price) and
        (params.checkin or params.checkout)
    )
    
    if has_comprehensive_info and len(message.split()) > 5:  # Long message with lots of details
        print(f"DEBUG - COMPREHENSIVE INFO: Need confirmation for detailed request")
        return False  # Require confirmation for comprehensive requests
    
    # 5. Auto-search for simple additions to existing info
    if params.location and not has_comprehensive_info:
        # Only auto-search if this is a simple addition, not comprehensive details
        simple_additions = [
            "center", "downtown", "cheap", "expensive", "budget", "close",
            "near", "apartment", "house", "studio"
        ]
        
        if any(addition in message_lower for addition in simple_additions) and len(message.split()) <= 3:
            print(f"DEBUG - AUTO SEARCH: Simple addition to existing info")
            return True
    
    print(f"DEBUG - No search triggered - will show confirmation")
    return False

def should_show_confirmation(params: SearchParams, conversation_history: list) -> bool:
    """
    Show confirmation for comprehensive requests to ensure accuracy.
    """
    
    # Must have location as minimum
    if not params.location:
        return False
    
    # Check if we recently showed a confirmation - don't repeat
    recent_conversation = ""
    if conversation_history:
        for msg in conversation_history[-5:]:  # Check last 5 messages
            if msg.get("sender") == "assistant":
                recent_conversation += msg.get("text", "").lower()
    
    confirmation_indicators = [
        "ready?", "correct?", "sound good?", "i'll search", "should i search",
        "would you like me to search", "confirm", "confirmation"
    ]
    
    if any(indicator in recent_conversation for indicator in confirmation_indicators):
        print("DEBUG - No confirmation: Already asked recently")
        return False
    
    # Show confirmation when we have good info that should be verified
    has_searchable_info = (
        params.location and (
            params.guests or 
            params.max_price or 
            params.min_price or
            params.checkin or
            params.checkout or
            params.property_type
        )
    )
    
    if has_searchable_info:
        print("DEBUG - Show confirmation: Have searchable information to verify")
        return True
    
    # Show confirmation if user just provided location only
    if params.location and not has_searchable_info:
        print("DEBUG - Show confirmation: Location only, need more details")
        return True
    
    print("DEBUG - No confirmation needed")
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