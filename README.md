# Stocksence - Stock Market Prediction & Analysis Platform

**Stocksence** is a comprehensive web-based stock market prediction and analysis platform built with Flask. It provides real-time market data, AI-powered price predictions, news analysis, and comprehensive market insights for Indian stock market (NSE) investors and traders.

---

## 🎯 Features

### Core Features
- **AI-Powered Price Predictions** — Two machine learning models (XGBoost & LSTM) for stock price forecasting
- **Real-Time Market Data** — Live market movers, top gainers/losers with cached data for performance
- **Stock Analysis** — Detailed stock information, historical data, and technical indicators
- **News & Sentiment Analysis** — Integrated news from Brave Search and company-specific headlines
- **User Authentication** — Secure signup/login with OTP verification and password reset
- **Intelligent Chat** — OpenAI-powered chatbot for stock market Q&A and insights
- **Responsive Dashboard** — User-friendly interface with market overview and personalized features

### Stock Market Coverage
- **10 Major NSE Companies:**
  - TCS, Reliance, Infosys, HDFC Bank, ICICI Bank
  - SBI, ITC, L&T, Axis Bank, Bharti Airtel

### API Endpoints
- `/api/market-movers` — Market gainers & losers
- `/api/stock-history` — Historical stock data
- `/api/predict` — AI price predictions (XGBoost/LSTM)
- `/api/company-news` — Company-specific news headlines
- `/api/chat` — OpenAI chatbot API

---

## 🏗️ Project Structure

```
stocksence/
├── app.py                    # Flask app initialization & configuration
├── routes.py                 # All route handlers & API endpoints
├── auth.py                   # User authentication & session management
├── config.py                 # Environment variables & API keys
├── email_service.py          # Email functionality (signup, password reset)
├── market_data.py            # Cached market data fetching & caching logic
├── stock_data.py             # NSE stock data fetching utilities
├── prediction_xgb.py         # XGBoost ML model for price predictions
├── prediction_lstm.py        # LSTM neural network for price predictions
├── nsetool.py                # NSE data tools & utilities
├── requirements.txt          # Python dependencies
├── templates/                # HTML templates
│   ├── base.html            # Base template (navbar, footer)
│   ├── index.html           # Home page
│   ├── login.html           # Login page
│   ├── signup.html          # Signup page
│   ├── signup_otp.html      # OTP verification
│   ├── forgot-password.html # Password reset
│   ├── dashboard.html       # User dashboard
│   ├── predict.html         # Stock prediction page
│   ├── info.html            # Stock info page
│   ├── news.html            # News feed
│   ├── about.html           # About page
│   ├── research/            # Research pages
│   └── errors/              # Error pages (404, 500)
├── static/                   # Static assets
│   └── images/
│       └── logos/           # Company logos
├── model/                    # ML models & training notebooks
│   ├── 10_Years_10_Companies.csv  # Training data
│   └── model2.ipynb         # Model training notebook
├── flask_session/           # Session storage
└── TROUBLESHOOTING.md       # Debugging guide
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Internet connection for real-time market data

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd stocksence
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=your-supabase-key
   NEWS_API_KEY=your-news-api-key
   BRAVE_API_KEY=your-brave-search-api-key
   OPENAI_API_KEY=your-openai-api-key
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   The app will be available at `http://localhost:5000`

---

## 📚 Key Technologies

### Backend
| Technology | Purpose |
|------------|---------|
| **Flask** | Web framework |
| **Flask-Session** | Server-side session management |
| **yfinance** | Stock market data fetching |
| **XGBoost** | Gradient boosting ML model |
| **TensorFlow/Keras** | LSTM neural network model |
| **scikit-learn** | Data preprocessing & ML utilities |
| **OpenAI API** | Chatbot & AI insights |
| **Supabase** | Database backend |
| **Brave Search API** | News aggregation |

### Frontend
- **HTML5/CSS3** — Responsive design
- **JavaScript** — Client-side interactivity
- **Jinja2** — Template rendering

---

## 🔐 Authentication & Security

### Features
- **Email-based Registration** — Signup with OTP verification
- **Secure Password Hashing** — bcrypt for password security
- **Session Management** — Flask-Session with file-based storage
- **Password Reset** — Email-based password recovery
- **Login Required Decorator** — Protected routes for authenticated users

### User Flow
1. User registers with email
2. OTP verification email sent
3. User enters OTP to confirm email
4. Account activated, user can login
5. Session created for authenticated access

---

## 🤖 ML Models

### XGBoost Model (`prediction_xgb.py`)
- **Type:** Gradient Boosting Regressor
- **Features:** Technical indicators (MA, RSI, MACD, etc.)
- **Input:** 1 year of historical stock data
- **Output:** Next-day/week price prediction with confidence

### LSTM Model (`prediction_lstm.py`)
- **Type:** Long Short-Term Memory Neural Network
- **Features:** Sequential price patterns
- **Input:** 60-day sliding window of closing prices
- **Output:** Price direction & magnitude prediction

### Model Selection
- Default model set in `app.config['DEFAULT_MODEL']` (0=XGBoost, 1=LSTM)
- Users can switch models in prediction interface
- Both models include error handling & retry logic

---

## 📊 Market Data & Caching

### Data Sources
- **yfinance** — Historical stock data, real-time quotes
- **NSE Tools** — NSE-specific market movers, indices
- **Brave Search API** — News aggregation & search
- **NewsAPI** — Alternative news source

### Caching Strategy
- **5-minute cache** for market movers (gainers/losers)
- Prevents API throttling and improves performance
- Automatic cache refresh on expiry
- Graceful fallback to cached data on API failures

---

## 🌐 API Endpoints

### Public Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page with market movers |
| `/about` | GET | About page |
| `/predict` | GET | Stock prediction interface |
| `/stocks` | GET | All stocks list |
| `/top-gainers` | GET | Top gaining stocks |
| `/top-losers` | GET | Top losing stocks |
| `/news` | GET | News feed |
| `/research` | GET | Research & educational content |

### Authenticated Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard` | GET | User dashboard |
| `/api/watchlist` | GET/POST/DELETE | Manage watchlist |

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/market-movers` | GET | Market gainers & losers (JSON) |
| `/api/stock-history` | GET | Historical stock data |
| `/api/predict` | GET | Price prediction endpoint |
| `/api/company-news` | GET | Company-specific news |
| `/api/chat` | POST | Chatbot API |

### Authentication Routes
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | GET/POST | User login |
| `/signup` | GET/POST | User registration |
| `/logout` | GET | User logout |
| `/forgot-password` | GET/POST | Password reset request |

---

## 🎨 User Interface

### Pages
- **Home** — Market overview with live gainers/losers
- **Predict** — Stock selection + prediction interface
- **Stock Info** — Detailed company information
- **News** — Aggregated market news
- **Dashboard** — Personalized user area
- **Chat** — AI-powered stock advisor
- **Research** — Educational resources & reports

### Responsive Design
- Mobile-friendly interface
- Adaptive layouts for tablets & desktops
- Fast load times with optimized assets

---

## 🛠️ Configuration

### Environment Variables
```env
# Flask
SECRET_KEY                # Session encryption key

# Database (Supabase)
SUPABASE_URL             # Supabase project URL
SUPABASE_KEY             # Supabase API key

# APIs
NEWS_API_KEY             # NewsAPI key
BRAVE_API_KEY            # Brave Search API key
OPENAI_API_KEY           # OpenAI API key

# Email Service
SMTP_SERVER              # Gmail SMTP server
SMTP_PORT                # SMTP port (usually 587)
EMAIL_ADDRESS            # Sender email
EMAIL_PASSWORD           # App password (not Gmail password)
```

### Flask Configuration (`app.py`)
```python
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['DEFAULT_MODEL'] = 0  # 0=XGBoost, 1=LSTM
```

---

## 📦 Dependencies

**Core Dependencies:**
- Flask 2.3.3
- Flask-SQLAlchemy 3.1.1
- Flask-Session 0.5.0
- Flask-CORS 4.0.0

**Data & ML:**
- yfinance 0.2.65
- pandas 2.1.4
- numpy 1.26.3
- scikit-learn
- xgboost
- tensorflow/keras (for LSTM)

**APIs & Utilities:**
- requests 2.31.0
- openai >= 1.0.0
- python-dotenv 1.0.0
- supabase-py

**Performance:**
- numexpr 2.8.7
- bottleneck 1.3.7

See `requirements.txt` for complete list with versions.

---

## 🐛 Troubleshooting

### Common Issues

**yfinance connection errors:**
- Check internet connection
- Verify ticker symbols (e.g., `TCS.ns` for NSE)
- Retry with exponential backoff (built-in)
- See `TROUBLESHOOTING.md`

**API key errors:**
- Verify all API keys in `.env` file
- Check API quotas & billing status
- Ensure keys have correct permissions

**Session/authentication issues:**
- Clear browser cookies
- Check `flask_session/` directory permissions
- Verify SECRET_KEY is set in `.env`

**Model prediction errors:**
- Ensure model files exist in `model/` directory
- Check feature engineering in `prediction_*.py`
- Verify yfinance data is not empty

See **TROUBLESHOOTING.md** for detailed debugging steps.

---

## 🚦 Development

### Running in Development Mode
```bash
python app.py
# or
flask run --debug
```

### Testing
```bash
python test.py
```

### Model Training
See `model/model2.ipynb` for XGBoost & LSTM model training notebooks.

### Code Structure
- **Routes** — All Flask routes in `routes.py`
- **Auth** — Authentication logic in `auth.py`
- **Predictions** — ML models in `prediction_*.py`
- **Data** — Market data logic in `market_data.py`, `stock_data.py`

---

## 📈 Future Enhancements

- **Watchlist & Portfolio Management** — User watchlists with price alerts
- **Advanced Charts** — Candlestick charts with technical indicators (SMA, EMA, Bollinger)
- **Backtesting Engine** — Test trading strategies against historical data
- **Mobile App** — Native iOS/Android applications
- **Real-time Streaming** — WebSocket updates for live prices
- **Advanced Analytics** — Correlation analysis, sector comparison
- **Social Features** — Share trades, follow expert traders
- **Risk Management** — Portfolio risk metrics, diversification analysis

---

## 📝 License

This project is proprietary software. All rights reserved.

---

## 👥 Support & Contact

For issues, questions, or feedback:
- 📧 Email: [contact@stocksence.com]
- 🐛 Bug reports: Submit via `/feedback` page
- 📚 Documentation: See TROUBLESHOOTING.md

---

## 📌 Notes

- **Market Hours:** NSE operates Monday-Friday, 9:15 AM - 3:30 PM IST
- **Data Freshness:** Market data cached for 5 minutes; real-time data via API
- **Predictions:** ML models are for educational purposes; not financial advice
- **Performance:** Cached data reduces API calls and improves response times

---

**Last Updated:** December 2025  
**Version:** 1.0.0
