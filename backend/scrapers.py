import re
import time
import requests
import os
from bs4 import BeautifulSoup
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import atexit

# Global driver cache for reuse
_driver_cache = None

def cleanup_driver():
    """Cleanup driver on exit"""
    global _driver_cache
    if _driver_cache:
        try:
            _driver_cache.quit()
        except:
            pass
        _driver_cache = None

# Register cleanup
atexit.register(cleanup_driver)

def get_chrome_options():
    """Get Chrome options optimized for Docker/production environment"""
    chrome_options = Options()
    
    # Basic headless options
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # PERFORMANCE OPTIMIZATIONS
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Skip loading images
    chrome_options.add_argument("--disable-javascript")  # Skip JS if possible
    chrome_options.add_argument("--disable-css")  # Skip CSS
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--aggressive-cache-discard")
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max-old-space-size=512")  # Reduce memory usage
    chrome_options.add_argument("--window-size=1024,768")  # Smaller window
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--fast-start")
    chrome_options.add_argument("--disable-background-networking")
    
    # Anti-detection
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Use system Chrome if available (Docker environment)
    chrome_binary = os.environ.get('CHROME_BIN') or os.environ.get('CHROME_PATH')
    if chrome_binary and os.path.exists(chrome_binary):
        chrome_options.binary_location = chrome_binary
        print(f"DEBUG - Using system Chrome: {chrome_binary}")
    
    return chrome_options

def scrape_airbnb_listings_selenium(search_url: str, max_listings: int = 3) -> List[Dict]:
    """Scrape Airbnb search results using Selenium for JavaScript rendering"""
    
    global _driver_cache
    
    try:
        # Reuse existing driver if available
        if _driver_cache:
            try:
                # Test if driver is still alive
                _driver_cache.current_url
                driver = _driver_cache
                print("DEBUG - Reusing existing Chrome driver")
            except:
                # Driver is dead, create new one
                _driver_cache = None
                driver = None
        else:
            driver = None
        
        # Create new driver if needed
        if not driver:
            print(f"DEBUG - Setting up new Selenium driver...")
            
            # Get optimized Chrome options
            chrome_options = get_chrome_options()
            
            # Setup driver with proper service
            try:
                # Try to use system ChromeDriver first (if available in Docker)
                service = Service()
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"DEBUG - System ChromeDriver failed, using webdriver-manager: {e}")
                # Fallback to webdriver-manager
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remove automation indicators
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Cache the driver for reuse
            _driver_cache = driver
        
        print(f"DEBUG - Attempting to scrape with Selenium: {search_url}")
        driver.get(search_url)
        
        # Wait for page to load
        print("DEBUG - Waiting for page to load...")
        time.sleep(1)
        
        # Wait for listings to appear
        try:
            WebDriverWait(driver, 5).until(  # Reduced from 10 to 5 seconds
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='card-container'], [aria-label*='listing'], .atm_9s_1txwivl"))
            )
            print("DEBUG - Listings found, proceeding to scrape...")
        except TimeoutException:
            print("DEBUG - Timeout waiting for listings, proceeding anyway...")
        
        # Try multiple selectors for listing containers
        selectors_to_try = [
            "[data-testid='card-container']",  # Primary listing card container
            "[role='group'][aria-label*='listing']",  # Listing groups
            "[role='group'][aria-label*='property']",  # Property groups  
            ".atm_9s_1txwivl[data-testid]",  # Elements with data-testid (more likely to be listings)
            ".l1ovpqvx",  # Another common listing class
            ".atm_gi_1n1ank9",  # Alternative listing container
        ]
        
        listings = []
        
        for selector in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"DEBUG - Selector '{selector}' found {len(elements)} elements")
                
                if elements:
                    listing_count = 0
                    for i, element in enumerate(elements):
                        if listing_count >= max_listings:
                            break
                            
                        try:
                            # Get element text to filter out non-listing elements
                            element_text = element.text.strip()
                            
                            # Skip search interface elements
                            skip_phrases = [
                                "Start your search", "Check in", "Check out", "Guests", 
                                "Filters", "filters applied", "Become a host", "Location",
                                "Homes in", "Total before taxes", "Display total before taxes"
                            ]
                            
                            is_ui_element = any(phrase in element_text for phrase in skip_phrases)
                            if is_ui_element or len(element_text) < 10:
                                print(f"DEBUG - Skipping UI element: {element_text[:100]}...")
                                continue
                                
                            listing_data = {}
                            
                            # First, let's see the element HTML for debugging (only for actual listings)
                            element_html = element.get_attribute('outerHTML')[:500]  # First 500 chars
                            print(f"DEBUG - Listing Element {listing_count+1} HTML: {element_html}")
                            print(f"DEBUG - Listing Element {listing_count+1} text: {element_text[:200]}...")
                            
                            # Extract title - look for property names
                            try:
                                title_selectors = [
                                    "[data-testid='listing-card-title']",
                                    ".atm_7l_jt7fhx",
                                    "h3",
                                    ".t1jojoys",
                                    "[role='heading']"
                                ]
                                title = None
                                for title_sel in title_selectors:
                                    try:
                                        title_elem = element.find_element(By.CSS_SELECTOR, title_sel)
                                        title_text = title_elem.text.strip()
                                        # Make sure it's actually a property title, not UI text
                                        if title_text and not any(phrase in title_text for phrase in skip_phrases):
                                            title = title_text
                                            break
                                    except NoSuchElementException:
                                        continue
                                
                                # If no title found, extract from element text (look for property-like text)
                                if not title:
                                    lines = element_text.split('\n')
                                    for line in lines[:3]:  # Check first few lines
                                        line = line.strip()
                                        if (len(line) > 5 and len(line) < 100 and 
                                            not any(phrase in line for phrase in skip_phrases) and
                                            not line.startswith('$') and not line.startswith('★')):
                                            title = line
                                            break
                                
                                listing_data['title'] = title or f"Property Listing {listing_count+1}"
                            except Exception as e:
                                listing_data['title'] = f"Property Listing {listing_count+1}"
                                print(f"DEBUG - Title extraction error: {e}")
                            
                            # Extract price - improved with element text search
                            try:
                                price_selectors = [
                                    "[data-testid='price-availability']",
                                    ".atm_7h_hxbz6r",
                                    ".a8jt5op", 
                                    "[aria-label*='price']",
                                    "span[aria-hidden='true']",  # Common for price text
                                    "span",  # Try all spans
                                    "div"    # Try all divs
                                ]
                                price = None
                                
                                # Try specific selectors first
                                for price_sel in price_selectors:
                                    try:
                                        price_elems = element.find_elements(By.CSS_SELECTOR, price_sel)
                                        for price_elem in price_elems:
                                            price_text = price_elem.text.strip()
                                            if '$' in price_text or '€' in price_text or '₽' in price_text:
                                                price = price_text
                                                print(f"DEBUG - Found price with selector '{price_sel}': {price}")
                                                break
                                        if price:
                                            break
                                    except NoSuchElementException:
                                        continue
                                
                                # If no specific selector worked, search in entire element text
                                if not price:
                                    # Look for price patterns in the entire element text
                                    price_patterns = [
                                        r'\$\d+[,.]?\d*(?:\s*per\s*night|\s*/\s*night|\s*night)?',
                                        r'€\d+[,.]?\d*(?:\s*per\s*night|\s*/\s*night|\s*night)?',
                                        r'₽\d+[,.]?\d*(?:\s*per\s*night|\s*/\s*night|\s*night)?',
                                        r'\$\d+',  # Simple dollar amount
                                        r'€\d+',   # Simple euro amount
                                        r'₽\d+'    # Simple ruble amount
                                    ]
                                    for pattern in price_patterns:
                                        match = re.search(pattern, element_text, re.IGNORECASE)
                                        if match:
                                            price = match.group(0)
                                            print(f"DEBUG - Found price with regex '{pattern}': {price}")
                                            break
                                
                                listing_data['price'] = price or "Price available on site"
                            except Exception as e:
                                listing_data['price'] = "Price available on site"
                                print(f"DEBUG - Price extraction error: {e}")
                            
                            # Extract rating - improved with element text search
                            try:
                                rating_selectors = [
                                    "[data-testid='listing-card-subtitle']",
                                    ".r1dxllyb",
                                    ".atm_3f_glywfm",
                                    "[aria-label*='rating']",
                                    "[aria-label*='star']",
                                    "span",  # Try all spans
                                    "div"    # Try all divs
                                ]
                                rating = None
                                
                                # Try specific selectors first
                                for rating_sel in rating_selectors:
                                    try:
                                        rating_elems = element.find_elements(By.CSS_SELECTOR, rating_sel)
                                        for rating_elem in rating_elems:
                                            rating_text = rating_elem.text.strip()
                                            # Look for star rating pattern
                                            if any(char.isdigit() for char in rating_text) and ('★' in rating_text or '⭐' in rating_text or 'star' in rating_text.lower() or re.search(r'\d+\.\d+', rating_text)):
                                                rating = rating_text
                                                print(f"DEBUG - Found rating with selector '{rating_sel}': {rating}")
                                                break
                                        if rating:
                                            break
                                    except NoSuchElementException:
                                        continue
                                
                                # If no specific selector worked, search in entire element text
                                if not rating:
                                    # Look for rating patterns in the entire element text
                                    rating_patterns = [
                                        r'\d+\.\d+\s*(?:★|⭐|stars?)',
                                        r'★\s*\d+\.\d+',
                                        r'⭐\s*\d+\.\d+',
                                        r'\d+\.\d+\s*\(\d+\)',  # 4.5 (123) format
                                        r'\d+\.\d+\s*•\s*\d+\s*reviews?',  # 4.5 • 123 reviews format
                                        r'\d+\.\d+'  # Simple decimal rating
                                    ]
                                    for pattern in rating_patterns:
                                        match = re.search(pattern, element_text, re.IGNORECASE)
                                        if match:
                                            rating = match.group(0)
                                            print(f"DEBUG - Found rating with regex '{pattern}': {rating}")
                                            break
                                
                                listing_data['rating'] = rating or "Rating not available"
                            except Exception as e:
                                listing_data['rating'] = "Rating not available"
                                print(f"DEBUG - Rating extraction error: {e}")
                            
                            # Extract link
                            try:
                                link_elem = element.find_element(By.CSS_SELECTOR, "a")
                                href = link_elem.get_attribute("href")
                                if href:
                                    if href.startswith('/'):
                                        listing_data['link'] = f"https://www.airbnb.com{href}"
                                    else:
                                        listing_data['link'] = href
                                else:
                                    listing_data['link'] = search_url
                            except:
                                listing_data['link'] = search_url
                            
                            listing_data['source'] = 'airbnb_selenium'
                            
                            print(f"DEBUG - Scraped listing {listing_count+1}: {listing_data['title'][:50]}... | {listing_data['price']} | {listing_data['rating']}")
                            listings.append(listing_data)
                            listing_count += 1  # Increment only for valid listings
                            
                        except Exception as e:
                            print(f"DEBUG - Error processing element {i+1}: {e}")
                            continue
                    
                    if listings:
                        print(f"DEBUG - Successfully scraped {len(listings)} real listings with selector '{selector}'")
                        break
                        
            except Exception as e:
                print(f"DEBUG - Error with selector '{selector}': {e}")
                continue
        
        if not listings:
            print("DEBUG - No listings found with Selenium, checking page content...")
            page_source = driver.page_source
            print(f"DEBUG - Page title: {driver.title}")
            print(f"DEBUG - Page source length: {len(page_source)}")
            print(f"DEBUG - First 1000 chars: {page_source[:1000]}")
            
            # Return redirect message instead of fake data
            listings = [
                {
                    'title': f'Properties available on Airbnb',
                    'price': 'Visit site for current pricing',
                    'rating': 'See reviews on Airbnb',
                    'link': search_url,
                    'source': 'airbnb_redirect'
                }
            ]
        
        return listings[:max_listings]
        
    except Exception as e:
        print(f"DEBUG - Selenium scraping error: {e}")
        return [
            {
                'title': f'Properties available on Airbnb',
                'price': 'Visit site for current pricing',
                'rating': 'See reviews on Airbnb', 
                'link': search_url,
                'source': 'airbnb_redirect'
            }
        ]
    
    finally:
        if driver:
            driver.quit()
            print("DEBUG - Selenium driver closed")

def scrape_airbnb_listings_requests(search_url: str, max_listings: int = 3) -> List[Dict]:
    """Fallback scraping method using requests and BeautifulSoup"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        print(f"DEBUG - Attempting to scrape: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=5)  # Reduced from 10 to 5 seconds
        print(f"DEBUG - Response status code: {response.status_code}")
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
                            'source': 'airbnb_requests'
                        })
                    except Exception as e:
                        print(f"DEBUG - Error extracting listing {j+1}: {e}")
                        continue
                
                if listings:
                    print(f"DEBUG - Successfully scraped {len(listings)} listings with selector '{selector}'")
                    break
        
        return listings[:max_listings]
        
    except Exception as e:
        print(f"DEBUG - Requests scraping error: {e}")
        return []

def scrape_airbnb_listings(search_url: str, max_listings: int = 3) -> List[Dict]:
    """Main scraping function that tries requests first (faster), then falls back to Selenium"""
    print(f"DEBUG - Starting scraping process for: {search_url}")
    
    import time
    start_time = time.time()
    max_total_time = 15  # Maximum 15 seconds total
    
    # Try requests first (much faster - 1-2 seconds vs 5-10 seconds)
    print("DEBUG - Trying fast requests method first...")
    try:
        results = scrape_airbnb_listings_requests(search_url, max_listings)
        if results and len(results) > 0:
            print("DEBUG - Requests scraping successful!")
            return results
    except Exception as e:
        print(f"DEBUG - Requests failed: {e}")
    
    # Check if we still have time for Selenium
    elapsed_time = time.time() - start_time
    if elapsed_time > max_total_time:
        print(f"DEBUG - Time limit exceeded ({elapsed_time:.1f}s), skipping Selenium")
        return generate_fallback_results(search_url)
    
    # Fallback to Selenium only if requests failed and we have time
    print("DEBUG - Falling back to Selenium method...")
    try:
        results = scrape_airbnb_listings_selenium(search_url, max_listings)
        if results and any('selenium' in result.get('source', '') for result in results):
            print("DEBUG - Selenium scraping successful!")
            return results
    except Exception as e:
        print(f"DEBUG - Selenium failed: {e}")
    
    # Final fallback
    return generate_fallback_results(search_url)

def generate_fallback_results(search_url: str) -> List[Dict]:
    """Generate fallback results when scraping fails"""
    print("DEBUG - All scraping methods failed, returning redirect message")
    location = "your location"
    if "/s/" in search_url:
        try:
            location = search_url.split("/s/")[1].split("/")[0].replace("-", " ").title()
        except:
            pass
    
    return [
        {
            'title': f'Properties available in {location}',
            'price': 'Visit Airbnb for current pricing',
            'rating': 'See actual reviews on site',
            'link': search_url,
            'source': 'airbnb_redirect'
        }
    ] 