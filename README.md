# Confind
**By Atay Kim**

*Your AI Assistant for Finding the Perfect Stay*

---

## What is Confind?

Confind is an intelligent travel assistant that revolutionizes how you search for accommodations. Instead of manually filtering through hundreds of Airbnb listings, you simply tell Confind what you're looking for in natural language—whether typed or spoken—and it finds, scrapes, and presents real properties with direct booking capabilities.

Think of it as having a personal travel agent who understands exactly what you want, speaks your language (literally—supports English and Russian), and can instantly pull up actual Airbnb listings with real prices, ratings, and availability.

## 🏗️ Tech Stack

**Frontend:**
- **React 18** with TypeScript for type safety
- **Vite** for lightning-fast development and builds
- **Tailwind CSS** for responsive, modern UI
- **Web Speech API** for voice recognition and synthesis
- **Vercel** for seamless frontend deployment

**Backend:**
- **FastAPI** (Python) for high-performance async API
- **Groq LLaMA 3.1** for intelligent natural language processing
- **BeautifulSoup + Selenium** for robust web scraping
- **Pydantic** for data validation and serialization
- **Render.com** for reliable backend hosting

**Key Libraries:**
- `speech-recognition` and `speechSynthesis` APIs for talk mode
- `requests` and `selenium` for dual-strategy web scraping
- `groq-python` for AI-powered parameter extraction
- `python-dotenv` for secure environment management

## 🔄 Workflow & How It Actually Works

### 1. **Smart Query Processing**
When you say something like *"Find me apartments in Istanbul for 3 people under $80 for June 15-20"*, here's what happens behind the scenes:

- **Language Detection:** Determines if this is a search query vs. casual chat
- **Parameter Extraction:** Uses LLaMA 3.1 to intelligently parse:
  - Location: "Istanbul"
  - Guests: 3 people  
  - Budget: Under $80/night
  - Dates: June 15-20, 2024
- **Validation:** Cleans and validates extracted data (handles common speech-to-text errors)

### 2. **Intelligent Search Triggering**
The system uses sophisticated logic to decide when to search:
- **Immediate Search:** Simple confirmations ("yes", "go", "find it")
- **Auto-Search:** When you provide location + any details
- **Confirmation:** Only for very complex requests (10+ words with multiple parameters)

This means less back-and-forth, more results.

### 3. **Real-Time Web Scraping**
We don't use fake data. Ever. When you search, we:
- **Generate Airbnb URLs** with your exact parameters (location, dates, guests, price filters)
- **Scrape Live Data** using a hybrid approach:
  - Primary: Fast `requests` with BeautifulSoup
  - Fallback: Selenium for JavaScript-heavy pages
  - Backup: Direct URL redirection if scraping fails
- **Extract Real Info:** Actual titles, prices, ratings, and booking links

### 4. **Voice-First Experience**
The talk mode isn't just a gimmick—it's computational efficiency:
- **Context-Aware Processing:** Fixes common speech-to-text errors automatically
- **Smart Turn-Taking:** Knows when you're done speaking vs. pausing
- **Auto-Correction:** "apartment in is tanble for 3 people" → "apartment in Istanbul for 3 people"
- **Bilingual Support:** Seamlessly switches between English and Russian

### 5. **Direct Booking Integration**
When you select a property, we generate authentic Airbnb URLs:
- **Message Host:** Direct link to contact the property owner
- **Book Now:** Takes you straight to Airbnb's booking page with your dates pre-filled
- **Secure:** All transactions happen on Airbnb.com for safety

## 🚀 Technical Considerations

### Performance Optimizations
- **Smart Caching:** Recent searches cached to avoid re-scraping
- **Parallel Processing:** Multiple scraping strategies run simultaneously
- **Token Limits:** AI responses capped at 300 tokens for speed
- **Conversation History:** Limited to last 6 messages to reduce processing time

### Error Handling & Resilience
- **Graceful Degradation:** If advanced scraping fails, falls back to simpler methods
- **Timeout Management:** 10-second fallbacks prevent UI from getting stuck
- **Rate Limiting:** Respectful scraping with delays to avoid being blocked
- **Error Recovery:** Talk mode automatically recovers from speech synthesis interruptions

### Data Accuracy
- **Real-Time Validation:** Prices, availability, and property details are live
- **Parameter Cleaning:** Handles edge cases like "$70 USD per day maximum" → max_price: 70
- **Date Parsing:** Supports multiple formats ("June 15-20", "6/15-6/20", "15-20 июня")
- **Guest Validation:** Prevents extraction errors (like confusing prices for guest counts)

### Security & Privacy
- **No Data Storage:** We don't store your search history or personal info
- **Secure APIs:** All AI processing uses encrypted Groq endpoints
- **Direct Routing:** Booking happens directly through Airbnb's secure platform
- **Environment Variables:** Sensitive keys stored securely, never in code

## 🎯 Key Features

- **🎤 Voice Interface:** Natural speech input with automatic error correction
- **🌍 Bilingual:** English and Russian support with one-click switching  
- **⚡ Real-Time Search:** Live Airbnb data, not outdated listings
- **🤖 Smart AI:** Understands context and handles complex requests
- **📱 Responsive Design:** Works perfectly on mobile and desktop
- **🔗 Direct Booking:** One-click access to actual Airbnb pages
- **⏱️ Fast Response:** Optimized for speed with <3 second typical response times

## 🛠️ Setup & Installation

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
export GROQ_API_KEY="your_groq_api_key"
python main.py
```

### Frontend Setup  
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
```bash
# Backend (.env)
GROQ_API_KEY=your_groq_api_key_here
PORT=10000

# Frontend (automatic via Vercel)
VITE_API_URL=https://your-backend.render.com
```

## 🌟 Why Confind?

Traditional booking sites make you click through endless filters and pages. Confind understands that in 2024, you should be able to just *say* what you want and get real results immediately.

Whether you're planning a weekend getaway or a month-long adventure, Confind makes finding the perfect place as easy as having a conversation.

---

*Built with ❤️ for the nFactorial AI Cup 2025*
