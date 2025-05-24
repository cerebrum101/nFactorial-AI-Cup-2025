#!/usr/bin/env python3
"""
Automated testing script for Condfind system
Runs systematic tests to detect common issues
"""

import requests
import json
import time
from typing import Dict, List, Any
from main import extract_search_params, build_airbnb_url, should_trigger_search

# Test cases from test_prompts.md
TEST_CASES = [
    {
        "name": "Simple Location",
        "input": "I need a place in Tokyo",
        "expected": {"location": "Tokyo"},
        "red_flags": ["help", "place", "need"]
    },
    {
        "name": "Complex Location", 
        "input": "Looking for accommodation in New York City",
        "expected": {"location": "New York City"},
        "red_flags": ["accommodation", "looking"]
    },
    {
        "name": "Location with Preposition",
        "input": "I'm traveling to San Francisco for work", 
        "expected": {"location": "San Francisco"},
        "red_flags": ["traveling", "work"]
    },
    {
        "name": "Help Request (No Location)",
        "input": "I need help finding a good apartment",
        "expected": {"location": None},
        "red_flags": ["help", "apartment", "finding"]
    },
    {
        "name": "Multiple Parameters",
        "input": "Need apartment in Berlin for 2 people, budget $100-150, with kitchen",
        "expected": {
            "location": "Berlin",
            "guests": 2,
            "min_price": 100,
            "max_price": 150,
            "amenities": ["kitchen"]
        },
        "red_flags": []
    },
    {
        "name": "Search Trigger Test",
        "input": "Please search for places in London",
        "expected": {"location": "London", "should_trigger": True},
        "red_flags": []
    }
]

def test_parameter_extraction():
    """Test parameter extraction logic"""
    print("🧪 Testing Parameter Extraction...")
    
    issues_found = []
    
    for test in TEST_CASES:
        print(f"  Testing: {test['name']}")
        
        # Extract parameters
        params = extract_search_params(test['input'])
        
        # Check expected values
        expected = test['expected']
        for key, expected_value in expected.items():
            if key == "should_trigger":
                continue  # Handle separately
                
            actual_value = getattr(params, key, None)
            
            if expected_value is None:
                if actual_value is not None:
                    issues_found.append(f"❌ {test['name']}: Expected {key}=None, got {actual_value}")
            elif isinstance(expected_value, list):
                if actual_value != expected_value:
                    issues_found.append(f"❌ {test['name']}: Expected {key}={expected_value}, got {actual_value}")
            else:
                if actual_value != expected_value:
                    issues_found.append(f"❌ {test['name']}: Expected {key}='{expected_value}', got '{actual_value}'")
        
        # Check for red flags (things that should NOT be extracted)
        for red_flag in test['red_flags']:
            if params.location and red_flag.lower() in params.location.lower():
                issues_found.append(f"🚩 {test['name']}: Red flag '{red_flag}' found in location: '{params.location}'")
        
        # Test search triggering
        if "should_trigger" in expected:
            should_search = should_trigger_search(test['input'].lower(), params)
            if should_search != expected["should_trigger"]:
                issues_found.append(f"❌ {test['name']}: Expected search trigger={expected['should_trigger']}, got {should_search}")
        
        if not issues_found:
            print(f"    ✅ Passed")
        else:
            for issue in issues_found:
                print(f"    {issue}")
    
    return issues_found

def test_url_generation():
    """Test URL generation logic"""
    print("\n🔗 Testing URL Generation...")
    
    issues_found = []
    
    url_tests = [
        {
            "name": "Basic URL",
            "input": "Apartment in Seattle for 3 people",
            "should_contain": ["/Seattle/homes", "adults=3"],
            "should_not_contain": ["/help/homes", "undefined"]
        },
        {
            "name": "Multiple Parameters",
            "input": "Villa in Barcelona for 4 people, $200-300, with pool",
            "should_contain": ["/Barcelona/homes", "adults=4", "price_min=200", "price_max=300"],
            "should_not_contain": ["/help/homes"]
        }
    ]
    
    for test in url_tests:
        print(f"  Testing: {test['name']}")
        
        params = extract_search_params(test['input'])
        if params.location:
            url = build_airbnb_url(params)
            
            # Check required components
            for required in test['should_contain']:
                if required not in url:
                    issues_found.append(f"❌ {test['name']}: URL missing '{required}': {url}")
            
            # Check forbidden components
            for forbidden in test['should_not_contain']:
                if forbidden in url:
                    issues_found.append(f"🚩 {test['name']}: URL contains forbidden '{forbidden}': {url}")
            
            print(f"    Generated: {url[:80]}...")
            
            if not any(required not in url for required in test['should_contain']) and \
               not any(forbidden in url for forbidden in test['should_not_contain']):
                print(f"    ✅ Passed")
        else:
            issues_found.append(f"❌ {test['name']}: No location extracted from '{test['input']}'")
    
    return issues_found

def test_api_endpoint(base_url="http://localhost:8000"):
    """Test the actual API endpoint"""
    print(f"\n🌐 Testing API Endpoint ({base_url})...")
    
    issues_found = []
    
    api_tests = [
        {
            "message": "I need a place in Tokyo for 2 people",
            "should_trigger_search": True,
            "check_for_fake_listings": True
        },
        {
            "message": "Help me find a good place",
            "should_trigger_search": False,
            "check_for_fake_listings": False
        }
    ]
    
    for test in api_tests:
        print(f"  Testing: {test['message']}")
        
        try:
            response = requests.post(f"{base_url}/chat", json={
                "message": test['message'],
                "conversation_history": []
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if search was triggered correctly
                has_results = data.get('search_results') is not None
                if has_results != test['should_trigger_search']:
                    issues_found.append(f"❌ API: Expected search trigger={test['should_trigger_search']}, got {has_results}")
                
                # Check for fake listings in AI response
                if test['check_for_fake_listings']:
                    response_text = data.get('response', '').lower()
                    fake_indicators = [
                        'cozy mountain view', 'mountain lodge', 'central apartment',
                        '$320', '$380', '$290'  # Specific fake prices
                    ]
                    
                    for indicator in fake_indicators:
                        if indicator in response_text:
                            issues_found.append(f"🚩 API: Detected fake listing indicator '{indicator}' in response")
                
                print(f"    ✅ API responded successfully")
                
            else:
                issues_found.append(f"❌ API: HTTP {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            issues_found.append(f"❌ API: Connection failed - {e}")
        
        time.sleep(1)  # Rate limiting
    
    return issues_found

def run_quick_checklist():
    """Run the quick checklist from test_prompts.md"""
    print("\n✅ Running Quick Checklist...")
    
    checklist_tests = [
        "Place in Tokyo for 2 people",
        "Help me find a house", 
        "Villa in Paris with pool under $200"
    ]
    
    all_issues = []
    
    for test_input in checklist_tests:
        print(f"  Quick test: {test_input}")
        
        # Test parameter extraction
        params = extract_search_params(test_input)
        
        # Test URL generation
        if params.location:
            url = build_airbnb_url(params)
            
            # Quick checks
            if "/help/homes" in url:
                all_issues.append(f"🚩 Quick test failed: '/help/homes' found in URL for '{test_input}'")
            elif params.location.lower() in url.lower():
                print(f"    ✅ Location correctly in URL")
            else:
                all_issues.append(f"❌ Quick test failed: Location '{params.location}' not found in URL")
        else:
            if "help" in test_input.lower():
                print(f"    ✅ Correctly no location extracted from help request")
            else:
                all_issues.append(f"❌ Quick test failed: No location extracted from '{test_input}'")
    
    return all_issues

def main():
    """Run all tests"""
    print("🚀 Starting Condfind System Tests\n")
    
    all_issues = []
    
    # Run all test categories
    all_issues.extend(test_parameter_extraction())
    all_issues.extend(test_url_generation())
    all_issues.extend(run_quick_checklist())
    
    # Try API tests (may fail if server not running)
    try:
        all_issues.extend(test_api_endpoint())
    except Exception as e:
        print(f"\n⚠️  API tests skipped (server not running?): {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*50}")
    
    if all_issues:
        print(f"❌ {len(all_issues)} issues found:")
        for issue in all_issues:
            print(f"  {issue}")
    else:
        print("✅ All tests passed! No issues detected.")
    
    print(f"\n💡 Next steps:")
    print(f"  1. Fix any issues listed above")
    print(f"  2. Test manually with the chat interface")
    print(f"  3. Re-run this script after changes")
    
    return len(all_issues)

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)  # Non-zero exit code if issues found 