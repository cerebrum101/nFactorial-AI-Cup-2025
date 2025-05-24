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
    Simplified logic to determine when to trigger search.
    Be much more aggressive about searching when we have basic info.
    """
    
    # Must have location as minimum requirement
    if not params.location:
        print("DEBUG - No search: Missing location")
        return False
    
    message_lower = message.lower().strip()
    
    # Simple affirmative responses - be VERY generous
    affirmative_responses = [
        "yes", "yep", "yeah", "ok", "okay", "sure", "go", "go ahead", 
        "do it", "correct", "that's right", "start searching", "search",
        "find", "let's go", "proceed", "continue", "good", "right", "fine",
        "perfect", "exactly", "sounds good", "looks good", "confirmed"
    ]
    
    # Check for simple affirmative responses
    if message_lower in affirmative_responses:
        print(f"DEBUG - Search triggered: Affirmative response '{message_lower}'")
        return True
    
    # Explicit search trigger phrases (high confidence)
    explicit_triggers = [
        "search", "find", "look for", "show me", "what's available",
        "can you search", "let's see", "ready to search", "search for",
        "find me", "show options", "what do you have", "let me see",
        "get me", "just get me", "under $", "under ", "max $", "budget",
        "do it again", "search again", "try again", "again", "repeat",
        "go", "start", "begin", "now"  # Added more trigger words
    ]
    
    has_explicit_trigger = any(phrase in message_lower for phrase in explicit_triggers)
    
    if has_explicit_trigger:
        print(f"DEBUG - Search triggered: Explicit request detected")
        return True
    
    # If user provided specific dates, prices, or details in this message, search immediately
    detail_indicators = [
        r"\d+\s*-\s*\d+\s*(?:june|july|august|may|april|march|january|february|september|october|november|december)",
        r"(?:june|july|august|may|april|march|january|february|september|october|november|december)\s*\d+",
        r"\$\d+", r"budget", r"max", r"fixed", r"exact", r"specific",
        r"\d+\s+(?:adults?|people|guests?)", r"for\s+\d+", r"\d+\s+of\s+us"
    ]
    
    for pattern in detail_indicators:
        if re.search(pattern, message_lower):
            print(f"DEBUG - Search triggered: Specific details provided")
            return True
    
    # NEW: Auto-trigger if we have location and ANY additional info (be more aggressive)
    if (params.location and 
        (params.guests or params.max_price or params.min_price or params.property_type) and
        not any(word in message_lower for word in ["no", "not", "don't", "wait", "stop", "first", "before"])):
        print(f"DEBUG - Auto-search triggered: Have location and additional details")
        return True
    
    # NEW: If user gives location + any specific request words, search immediately
    if (params.location and 
        any(word in message_lower for word in ["close to", "center", "downtown", "near", "area", "district", "neighborhood"]) and
        not any(word in message_lower for word in ["no", "not", "don't", "wait", "stop"])):
        print(f"DEBUG - Search triggered: Location + area specification")
        return True
    
    print(f"DEBUG - No search triggered")
    return False

def should_show_confirmation(params: SearchParams, conversation_history: list) -> bool:
    """
    Much more restrictive confirmation logic.
    Almost never show confirmations - just search immediately.
    """
    
    # Must have location as minimum
    if not params.location:
        return False
    
    # Check if we recently showed a confirmation - look at last 5 messages
    recent_conversation = ""
    if conversation_history:
        for msg in conversation_history[-5:]:  # Increased from 3 to 5
            if msg.get("sender") == "assistant":
                recent_conversation += msg.get("text", "").lower()
    
    # Don't show confirmation again if we EVER showed it recently
    confirmation_indicators = [
        "is this correct", "should i start searching", "would you like me to search",
        "ready to search", "does this look good", "confirm these details",
        "search for", "does this sound right", "correct?", "right?",
        "shall i", "should i", "ready to", "confirmation", "confirm"
    ]
    
    if any(indicator in recent_conversation for indicator in confirmation_indicators):
        print("DEBUG - Confirmation already shown recently")
        return False
    
    # Calculate completeness score
    info_completeness_score = 0
    if params.location: info_completeness_score += 2
    if params.guests: info_completeness_score += 1
    if params.min_price or params.max_price: info_completeness_score += 1
    if params.property_type: info_completeness_score += 0.5
    if params.amenities: info_completeness_score += 0.5
    
    # ALMOST NEVER confirm - only for extremely complex requests
    # Most searches should happen immediately without confirmation
    if info_completeness_score >= 6:  # Very high threshold - was 4, now 6
        print(f"DEBUG - Should show confirmation: completeness score {info_completeness_score}")
        return True
    
    print(f"DEBUG - Not showing confirmation: score {info_completeness_score} (need 6+)")
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