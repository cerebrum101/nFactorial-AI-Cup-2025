# Condfind System Testing Prompts

## Purpose
This document contains systematic test prompts designed to identify common issues in the Condfind AI + Airbnb search system.

## Test Categories

### 1. Location Extraction Tests

**Test 1.1: Simple Location Mentions**
```
Input: "I need a place in Tokyo"
Expected: location="Tokyo"
Watch for: location="place" or location="need"
```

**Test 1.2: Complex Location Names**
```
Input: "Looking for accommodation in New York City"
Expected: location="New York City" 
Watch for: location="accommodation" or truncated location
```

**Test 1.3: Location with Prepositions**
```
Input: "I'm traveling to San Francisco for work"
Expected: location="San Francisco"
Watch for: location="work" or location="traveling"
```

**Test 1.4: Locations with Country/State**
```
Input: "I want to stay in Paris, France for 3 nights"
Expected: location="Paris, France" or location="Paris"
Watch for: location="stay" or location="nights"
```

**Test 1.5: Tricky Non-Locations**
```
Input: "I need help finding a good apartment"
Expected: location=None (should not extract "help" or "apartment")
Watch for: location="help" or location="apartment"
```

### 2. Parameter Extraction Tests

**Test 2.1: Guest Count Extraction**
```
Input: "Apartment in Miami for 4 people"
Expected: location="Miami", guests=4
Watch for: guests=None or wrong number
```

**Test 2.2: Budget Range Extraction**
```
Input: "House in Austin under $200 per night"
Expected: location="Austin", max_price=200
Watch for: price extracted as location
```

**Test 2.3: Property Type Extraction**
```
Input: "Looking for a villa in Bali with pool"
Expected: location="Bali", property_type="villa", amenities=["pool"]
Watch for: property_type=None when clearly mentioned
```

**Test 2.4: Multiple Parameters**
```
Input: "Need apartment in Berlin for 2 people, budget $100-150, with kitchen"
Expected: location="Berlin", guests=2, min_price=100, max_price=150, amenities=["kitchen"]
Watch for: Missing any of these parameters
```

### 3. Search Triggering Tests

**Test 3.1: Explicit Search Request**
```
Input: "Please search for places in London"
Expected: should_trigger_search=True
Watch for: No search triggered despite explicit request
```

**Test 3.2: Sufficient Info Without Trigger Words**
```
Input: "Tokyo apartment for 2 people under $100"
Expected: should_trigger_search=True (has location + guests + budget)
Watch for: Search not triggered despite having enough info
```

**Test 3.3: Insufficient Info**
```
Input: "I need a nice place with good reviews"
Expected: should_trigger_search=False (no location)
Watch for: Search triggered without location
```

### 4. URL Generation Tests

**Test 4.1: Basic URL Structure**
```
Input: "Apartment in Seattle for 3 people"
Expected URL should contain: 
- "/s/Seattle/homes" (not "/s/help/homes")
- "adults=3"
- Proper encoding
Watch for: "help" in URL, malformed encoding
```

**Test 4.2: Special Characters in Location**
```
Input: "Place in São Paulo, Brazil"
Expected: Proper URL encoding of special characters
Watch for: Broken encoding, invalid URLs
```

**Test 4.3: All Parameters URL**
```
Input: "Villa in Barcelona for 4 people, $200-300, with pool and parking"
Expected URL should contain all filters properly encoded
Watch for: Missing parameters, malformed query strings
```

### 5. AI Response Behavior Tests

**Test 5.1: Real vs Fake Listings**
```
Test: After search is triggered, check if AI invents listings
Expected: AI should only reference actual search results
Watch for: AI creating fake listings with fake prices/ratings
Red flags: Specific fake details like "Cozy Mountain View Apartment $320"
```

**Test 5.2: No Results Handling**
```
Test: When scraping fails or returns empty
Expected: AI acknowledges limited results, doesn't invent data
Watch for: AI pretending to have results when there are none
```

**Test 5.3: Response Format Consistency**
```
Expected: Search results displayed in frontend cards + AI commentary
Watch for: AI duplicating the listing info in text form
```

### 6. Edge Cases and Error Handling

**Test 6.1: Ambiguous Locations**
```
Input: "I want to visit London"
Issues to spot: 
- Which London? (Ontario vs UK)
- Should ask for clarification
```

**Test 6.2: Invalid Dates**
```
Input: "Place in Miami from yesterday to tomorrow"
Expected: Handle gracefully, use default dates
Watch for: System crashes or invalid date URLs
```

**Test 6.3: Extreme Budgets**
```
Input: "Luxury villa in Monaco under $10"
Expected: Handle unrealistic constraints gracefully
Watch for: System errors or nonsensical results
```

**Test 6.4: Non-English Locations**
```
Input: "Apartment in 北京" (Beijing in Chinese)
Expected: Handle gracefully or ask for English name
Watch for: System crashes or encoding issues
```

### 7. Integration Tests

**Test 7.1: Full Conversation Flow**
```
Conversation:
User: "Hi, I need accommodation"
AI: Should ask for details
User: "In Barcelona"  
AI: Should ask for more details
User: "For 2 people next week"
AI: Should now trigger search (has location + guests)
Expected: Search triggers at the right moment
```

**Test 7.2: Search Refinement**
```
After initial search:
User: "Show me cheaper options"
Expected: New search with adjusted price filter
Watch for: Same results shown again
```

## Quick Issue Detection Checklist

Run this after any changes:

1. **"Place in Tokyo for 2 people"** 
   - ✅ URL contains "/Tokyo/homes"
   - ✅ URL contains "adults=2"
   - ✅ No fake listings in AI response

2. **"Help me find a house"**
   - ✅ No location extracted
   - ✅ No search triggered
   - ✅ AI asks for more info

3. **"Villa in Paris with pool under $200"**
   - ✅ All parameters extracted correctly
   - ✅ Search triggered automatically
   - ✅ Real Airbnb URL generated

4. **Check debug output for:**
   - ✅ Location extraction working
   - ✅ URL generation correct
   - ✅ No "help" in URLs
   - ✅ Proper parameter encoding

## Common Red Flags

- **URL contains "/help/homes"** → Location extraction broken
- **AI mentions specific fake properties** → AI hallucinating results  
- **Same URL for different searches** → Parameter extraction not working
- **Search triggered without location** → Trigger logic broken
- **No search when clearly should** → Trigger too restrictive 