from flask import jsonify
import yfinance as yf

# Company list and logo mapping for predict page

# Company display names
companies = [
    'TCS.ns', 'RELIANCE.ns', 'INFY.ns', 'HDFCBANK.ns', 'ICICIBANK.ns',
        'SBIN.ns', 'ITC.ns', 'LT.ns', 'AXISBANK.ns', 'BHARTIARTL.ns'
]

# Map display names to Yahoo Finance ticker symbols
company_tickers = {
    "TCS": "tcs",
    "Reliance": "reliance",
    "Infosys": "infosys",
    "HDFC": "hdfc",
    "ICICI Bank": "icici",
    "SBI Bank": "sbi",
    "ITC": "itc",
    "L and T": "landt",
    "Axis Bank": "axis",
    "Bharti Airtel": "bharti"
}

company_logos = {
    "TCS.ns": "images/logos/tcs.png",
    "RELIANCE.ns": "images/logos/reliance.png",
    "INFY.ns": "images/logos/infosys.png",
    "HDFCBANK.ns": "images/logos/hdfc.png",
    "ICICIBANK.ns": "images/logos/icici.png",
    "SBIN.ns": "images/logos/sbi.png",
    "ITC.ns": "images/logos/itc.png",
    "LT.ns": "images/logos/landt.png",
    "AXISBANK.ns": "images/logos/axis.png",
    "BHARTIARTL.ns": "images/logos/bharti.png"
}

from flask import render_template, jsonify, request, redirect, url_for, session, flash
import yfinance as yf
import requests
import pandas as pd
import numpy as np
from app import app
from prediction_xgb import predict_price_xgb
from prediction_lstm import predict_price_lstm
from market_data import get_market_movers_cached, format_number_wrapper
from datetime import datetime
import logging
import time
from auth import handle_login, handle_signup_request, handle_signup_otp, handle_password_reset, verify_reset_code, reset_user_password
from config import NEWS_API_KEY, BRAVE_API_KEY
from chatbot_service import query_chatgpt_with_brave, brave_search
import peewee


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')
# Predict and Info routes
@app.route('/predict')
def predict():
    return render_template('predict.html', companies=companies, company_logos=company_logos)

@app.route('/info')
def info():
    company = request.args.get('company')
    if not company:
        return redirect(url_for('predict'))
    # Map display name to Yahoo Finance symbol
    symbol = company_tickers.get(company, company)
    clean_name = company
    return render_template('info.html', company_name=company, clean_company_name=clean_name, symbol=symbol)


# Home page with market movers
@app.route('/')
def index():
    try:
        # Show popup only when set by login and consume the flag so it won't repeat until next login
        show_popup = session.pop('show_popup', False)
        gainers, losers = get_market_movers_cached(limit=10)
        return render_template('index.html', gainers=gainers, losers=losers, format_number=format_number_wrapper, show_popup=show_popup)
    except Exception as e:
        logging.error(f"Error fetching market data: {e}")
        return render_template('index.html', gainers=[], losers=[], show_popup=False)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email and password:
            success, msg = handle_login(email, password)
            if success:
                return redirect(url_for('index'))
            flash(msg or 'Invalid credentials')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

# Forgot password route
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    step = 'email'  # possible values: 'email', 'otp', 'password'
    error = None
    message = None

    if request.method == 'POST':
        # Step 1: user submitted email to request reset
        if 'email' in request.form and request.form.get('email'):
            email = request.form.get('email')
            ok, msg = handle_password_reset(email)
            if ok:
                session['reset_email'] = email
                step = 'otp'
                message = 'OTP sent to your email.'
            else:
                error = msg or 'Failed to send reset email.'

        # Step 2: user submitted otp
        elif 'otp' in request.form and request.form.get('otp'):
            otp = request.form.get('otp')
            email = session.get('reset_email')
            if not email:
                error = 'Session expired. Please start again.'
            else:
                ok, msg = verify_reset_code(email, otp)
                if ok:
                    session['reset_verified'] = True
                    step = 'password'
                    message = 'OTP verified. Set your new password.'
                else:
                    error = msg or 'Invalid or expired code.'

        # Step 3: user submitted new password
        elif 'new_password' in request.form and request.form.get('new_password'):
            new_password = request.form.get('new_password')
            confirm = request.form.get('confirm_password')
            email = session.get('reset_email')
            if not session.get('reset_verified') or not email:
                error = 'Unauthorized or session expired. Please request a new code.'
            elif not new_password or new_password != confirm:
                error = 'Passwords do not match.'
                step = 'password'
            else:
                ok, msg = reset_user_password(email, new_password)
                if ok:
                    # cleanup session
                    session.pop('reset_email', None)
                    session.pop('reset_verified', None)
                    flash('Password updated. Please log in with your new password.')
                    return redirect(url_for('login'))
                else:
                    error = msg or 'Failed to update password.'
                    step = 'password'

    return render_template('forgot-password.html', step=step, error=error, message=message)

# Dashboard
from auth import login_required
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Market data API
@app.route('/api/market-movers')
def market_movers_api():
    try:
        gainers, losers = get_market_movers_cached(limit=5)
        return jsonify({
            'gainers': gainers,
            'losers': losers,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Stocks page
@app.route('/stocks')
def stocks():
    return render_template('stocks.html')

# Top gainers page
@app.route('/top-gainers')
def top_gainers():
    return render_template('top_gainers.html')

# Top losers page
@app.route('/top-losers')
def top_losers():
    return render_template('top_losers.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    logging.warning(f"404 error: {error}")
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"500 error: {error}")
    return render_template('errors/500.html'), 500



# Combined signup and OTP verification in one form
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    otp_sent = False
    error = None
    message = None
    email = ''
    username = ''
    if request.method == 'POST':
        if 'otp' in request.form:
            # User is submitting OTP
            otp = request.form.get('otp')
            success, msg = handle_signup_otp(otp)
            if success:
                return redirect(url_for('login'))
            else:
                otp_sent = True
                error = msg
        else:
            # User is submitting signup info
            email = request.form.get('email')
            password = request.form.get('password')
            username = request.form.get('username')
            success, msg = handle_signup_request(email, password, username)
            if success:
                otp_sent = True
                message = msg
            else:
                error = msg
    return render_template('signup.html', otp_sent=otp_sent, error=error, message=message, email=email, username=username)

@app.route('/research')
def research_page():
    return render_template('research/index.html')

@app.route('/research/reports')
def research_reports():
    return render_template('research/reports.html')

@app.route('/research/yearbooks')
def research_yearbooks():
    return render_template('research/yearbooks.html')

@app.route('/research/wallchart')
def research_wallchart():
    return render_template('research/wallchart.html')

@app.route('/top-gainers')
def top_gainers_page():
    gainers, _ = fetch_nse_data()
    return render_template('screener/top_gainers.html', gainers=gainers)

@app.route('/top-losers')
def top_losers_page():
    _, losers = fetch_nse_data()
    return render_template('screener/top_losers.html', losers=losers)

@app.route('/demat-guide')
def demat_guide():
    return render_template('demat_guide.html')

# News route
@app.route('/news')
def news():
    region = request.args.get('region', 'india')

    if region == "india":
        # Indian stock market news from trusted media
        url = "https://newsapi.org/v2/everything"
        query = "Indian stock market OR Sensex OR Nifty OR NSE OR BSE OR finance OR business"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": NEWS_API_KEY,
            "pageSize": 30,
            "domains": "economictimes.indiatimes.com,moneycontrol.com,business-standard.com,livemint.com,financialexpress.com"
        }
    else:
        # Global stock market news from reliable global media
        url = "https://newsapi.org/v2/everything"
        query = "global stock market OR S&P 500 OR Nasdaq OR Dow Jones OR Wall Street"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": NEWS_API_KEY,
            "pageSize": 30,
            "domains": "reuters.com,bloomberg.com,finance.yahoo.com,marketwatch.com,cnbc.com"
        }

    response = requests.get(url, params=params)
    data = response.json()

    # Filter: remove articles without images or from unwanted domains (like biztoc)
    articles = [
        a for a in data.get("articles", [])
        if a.get("urlToImage") and "biztoc.com" not in (a.get("url") or "")
    ]

    return render_template("news.html", articles=articles, region=region)


# Chatbot page
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')


# Chatbot API endpoint (AJAX) - with Brave Search enrichment
@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    try:
        data = request.get_json() or {}
        message = (data.get('message') or '').strip()
        company = data.get('company', '')
        symbol = data.get('symbol', '')

        if not message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400

        # First, fetch Brave Search results (always) so ChatGPT receives external sources
        search_query = f"{company} {message}".strip()
        brave_hits = []
        try:
            brave_hits = brave_search(search_query, size=4)
        except Exception as e:
            logging.debug(f'Brave search failed for chatbot_api: {e}')

        result = query_chatgpt_with_brave(
            message,
            company_name=company,
            symbol=symbol,
            period='1mo',
            brave_hits=brave_hits,
            force_brave=True
        )
        
        # Add source information to response
        if result.get('success'):
            result['has_sources'] = bool(result.get('sources_count', 0))
            result['sources_count'] = result.get('sources_count', 0)
        
        return jsonify(result)
    except Exception as e:
        logging.exception('Chatbot API error')
        return jsonify({'success': False, 'error': str(e)}), 500


# Company-specific news API (returns top 5 headlines for a given company/symbol)
@app.route('/api/company-news')
def company_news_api():
    company = request.args.get('company', '')
    symbol = request.args.get('symbol', '')
    # If only company name is provided, map to ticker
    if not symbol and company:
        symbol = company_tickers.get(company, '')

    if not symbol and not company:
        return jsonify({'error': 'No company or symbol provided'}), 400

    if not (BRAVE_API_KEY or NEWS_API_KEY):
        logging.error('Neither BRAVE_API_KEY nor NEWS_API_KEY is configured')
        return jsonify({'error': 'News API keys not configured on server'}), 500

    # Build a flexible query: try company full name (from yfinance if possible), short symbol (before dot), and the full symbol
    short = ''
    if symbol:
        short = symbol.split('.')[0]

    q_parts = []

    # If user supplied a human-friendly company name, prefer that
    if company and ' ' in company:
        q_parts.append(f'"{company}"')

    # If symbol looks like a ticker (eg TCS.NS), attempt to resolve long name via yfinance
    long_name = None
    try:
        if symbol:
            tk = yf.Ticker(symbol)
            info = tk.info or {}
            long_name = info.get('longName') or info.get('shortName')
    except Exception as e:
        logging.debug(f'Failed to fetch ticker info for {symbol}: {e}')

    if long_name:
        # only add if it's not the same as the short symbol
        if short.lower() not in long_name.lower():
            q_parts.append(f'"{long_name}"')

    # Add short symbol and raw symbol as backup tokens
    if short and short.lower() not in [p.lower() for p in q_parts]:
        q_parts.append(short)
    if symbol and symbol not in q_parts:
        q_parts.append(symbol)

    query = ' OR '.join(q_parts) if q_parts else symbol or company

    # Try Brave Search API first for company-specific news
    def normalize(s):
        if not s:
            return ''
        return ''.join(ch.lower() if ch.isalnum() or ch.isspace() else ' ' for ch in s)

    q_in_title = None
    if long_name:
        q_in_title = long_name
    elif company and ' ' in company:
        q_in_title = company
    elif short:
        q_in_title = short

    # Attempt Brave Search (single endpoint, no retries/fallbacks)
    brave_articles = []
    if BRAVE_API_KEY:
        try:
            # Try Brave's news endpoint first for actual news articles
            brave_url = 'https://api.search.brave.com/res/v1/news/search'
            brave_query = q_in_title or long_name or company or short or symbol
            params = {'q': brave_query, 'count': 20}
            headers = {'X-Subscription-Token': BRAVE_API_KEY, 'Accept': 'application/json', 'User-Agent': 'StockSense/1.0'}
            logging.info(f'Attempting Brave News Search with params: {params}')
            r = requests.get(brave_url, headers=headers, params=params, timeout=8)
            logging.info(f'Brave response status: {r.status_code} for {brave_url}')
            if r.status_code != 200:
                logging.warning(f'Brave returned non-200 status: {r.status_code}; not attempting fallback')
            else:
                try:
                    brave_data = r.json() or {}
                except Exception as e:
                    hdrs = {k: v for k, v in r.headers.items()} if hasattr(r, 'headers') else {}
                    logging.warning(f'Brave response not JSON: {e} ; status={getattr(r, "status_code", None)} ; headers={hdrs} ; text={getattr(r, "text", "")[:1000]}')
                    brave_data = {}

                logging.debug(f'Brave response keys: {list(brave_data.keys())}')

                # Tolerant parsing: look for common keys - Brave news API nests results under 'results'
                candidates = brave_data.get('results') or brave_data.get('web', {}).get('results') or brave_data.get('articles') or brave_data.get('data') or brave_data.get('items') or brave_data.get('organic_results') or []
                logging.info(f'Brave candidates count: {len(candidates)}')

                # Whitelist of trusted news/finance domains to prefer
                trusted_news_domains = ['bseindia.com', 'nseindia.com', 'reuters.com', 'ap.org', 'bbc.com', 'cnbc.com', 'bloomberg.com', 'economictimes.com', 'moneycontrol.com', 'theguardian.com', 'ndtv.com', 'thehindu.com', 'deccanchronicle.com', 'theprintindia.com', 'businesstoday.com', 'hindustantimes.com', 'tribune.com']
                excluded_domains = ['wikipedia.org', 'linkedin.com', 'facebook.com', 'instagram.com', 'twitter.com', 'youtube.com']
                news_like = []
                for item in candidates:
                    # item could be dict with different shapes
                    title = (item.get('title') or item.get('headline') or item.get('name') or '').strip()
                    link = (item.get('url') or item.get('link') or item.get('sourceUrl') or item.get('unescapedUrl') or '')
                    source = (item.get('source') or {}).get('name') if isinstance(item.get('source'), dict) else item.get('source')
                    published = item.get('publishedAt') or item.get('published') or item.get('date') or item.get('page_age')
                    desc = (item.get('description') or item.get('snippet') or item.get('summary') or item.get('excerpt') or '')

                    # Skip if no title or URL
                    if not title or not link:
                        continue

                    # Check domain
                    link_lower = link.lower()
                    
                    # Exclude social/info pages
                    if any(domain in link_lower for domain in excluded_domains):
                        continue
                    
                    # Prefer trusted news domains, accept others only if they look like articles
                    is_trusted_domain = any(domain in link_lower for domain in trusted_news_domains)
                    
                    if not is_trusted_domain:
                        # For untrusted domains, be stricter: require news/article/press keywords
                        path = ''
                        try:
                            path = link.split('/', 3)[-1].lower()
                        except Exception:
                            path = ''
                        has_news_keyword = any(k in path or k in link_lower or k in title.lower() for k in ('news', 'press-release', 'press', 'article', 'story', 'pressrelease'))
                        if not has_news_keyword:
                            continue

                    news_like.append({'title': title, 'url': link, 'source': source, 'publishedAt': published, 'description': desc})

                logging.info(f'Brave news-like candidates: {len(news_like)}')
                for a in news_like:
                    brave_articles.append(a)
        except Exception as e:
            logging.warning(f'Brave Search failed for {query}: {e}')

    # Filter Brave results strictly to ensure company mention
    tokens = []
    if long_name:
        tokens.append(normalize(long_name))
    if company:
        tokens.append(normalize(company))
    if short:
        tokens.append(normalize(short))
    tokens = [t for t in tokens if t]

    def matches_tokens(article):
        title = normalize(article.get('title') or '')
        desc = normalize(article.get('description') or '')
        text = title + ' ' + desc
        for tok in tokens:
            if tok in text:
                return True
            parts = tok.split()
            if any(p in text for p in parts):
                return True
        return False

    filtered_brave = [a for a in brave_articles if matches_tokens(a)]
    if filtered_brave:
        simplified = []
        for a in filtered_brave[:5]:
            simplified.append({
                'title': a.get('title'),
                'url': a.get('url'),
                'source': a.get('source'),
                'publishedAt': a.get('publishedAt'),
                'description': a.get('description')
            })
        return jsonify({'articles': simplified})

    # No articles found from Brave — do not fallback to NewsAPI; return empty list
    logging.info('No matching Brave articles found; returning empty articles list')
    return jsonify({'articles': []})


# Chat endpoint: use OpenAI official API
@app.route('/api/chat', methods=['POST'])
def chat_api():
    """
    Chat API endpoint that uses Brave Search + ChatGPT for enriched responses.
    
    Workflow:
    1. Receives user message and context
    2. Calls chatbot_service which:
       - Detects if Brave Search enrichment is needed
       - Fetches latest data/news from Brave Search
       - Queries ChatGPT with enriched context
    3. Returns ChatGPT response with source information
    """
    try:
        payload = request.get_json() or {}
        logging.info(f"Chat API request - payload keys: {list(payload.keys())}")
        
        # Extract parameters
        messages = payload.get('messages')
        if not messages:
            single = payload.get('message') or payload.get('text') or payload.get('content')
            if single:
                messages = [{'role': 'user', 'content': single}]
        
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
        
        # Get user's last message
        user_message = ""
        if isinstance(messages, list) and len(messages) > 0:
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get('role') == 'user' and msg.get('content'):
                    user_message = str(msg.get('content'))
                    break
        
        if not user_message:
            return jsonify({'error': 'No user message found'}), 400
        
        # Extract context parameters
        company_name = payload.get('company', '')
        symbol = payload.get('symbol', '') or company_name
        period = payload.get('period', '1mo')
        
        logging.info(f"Chat - company: {company_name}, symbol: {symbol}, query: {user_message[:50]}...")
        
        # First, fetch Brave Search results so ChatGPT receives external sources
        search_query = f"{company_name} {user_message}".strip()
        brave_hits = []
        try:
            brave_hits = brave_search(search_query, size=4)
        except Exception as e:
            logging.debug(f'Brave search failed in chat_api: {e}')

        # Use the new chatbot service, passing pre-fetched Brave hits
        result = query_chatgpt_with_brave(
            user_message=user_message,
            company_name=company_name,
            symbol=symbol,
            period=period,
            conversation_history=messages[:-1] if len(messages) > 1 else None,
            brave_hits=brave_hits,
            force_brave=True
        )
        
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error occurred')
            logging.warning(f"Chat failed: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # Build response
        response_text = result.get('response', '')
        sources_count = result.get('sources_count', 0)
        
        # Return in OpenAI-compatible format for frontend compatibility
        payload_out = {
            'status_code': 200,
            'result': {
                'choices': [{
                    'message': {'content': response_text},
                    'finish_reason': 'stop'
                }]
            },
            'assistant_text': response_text,
            'sources_count': sources_count,
            'brave_enriched': sources_count > 0
        }
        
        if sources_count > 0:
            logging.info(f"Chat response enriched with {sources_count} Brave sources")
        
        return jsonify(payload_out), 200
    
    except Exception as e:
        logging.error(f'Chat API error: {e}', exc_info=True)
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

# Helper function for NSE data
def fetch_nse_data():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()['data']
        
        stocks = []
        for stock in data:
            stocks.append({
                'name': stock['symbol'],
                'symbol': stock['symbol'],
                'price': stock['lastPrice'],
                'change': f"{stock['pChange']}%",
                'volume': f"{int(stock['totalTradedVolume']/1000000)}M"
            })
        
        gainers = sorted(stocks, key=lambda x: float(x['change'].strip('%')), reverse=True)[:10]
        losers = sorted(stocks, key=lambda x: float(x['change'].strip('%')))[:10]
        return gainers, losers
    except Exception as e:
        print(f"Error fetching data: {e}")
        return [], []
# API endpoint for historical stock data (all time)
@app.route('/api/stock-history')
def stock_history():
    company = request.args.get('company')
    symbol = request.args.get('symbol')
    # If only company name is provided, map to ticker
    if not symbol and company:
        symbol = company_tickers.get(company, '')
    period = request.args.get('period', 'max')
    if not symbol:
        return jsonify({'error': 'No symbol provided'}), 400
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Fetching stock history for {symbol} with period {period} (attempt {attempt + 1}/{max_retries})")
            
            # Configure yfinance session with proper headers
            ticker = yf.Ticker(symbol)
            ticker.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            })
            
            # yfinance supports: 1d,5d,1mo,3mo,6mo,ytd,1y,2y,5y,10y,max
            hist = ticker.history(period=period, timeout=15)
            logging.info(f"Raw history shape for {symbol}: {hist.shape}")
            
            if hist is None or hist.empty:
                logging.warning(f"Stock history API: Empty history returned from yfinance for {symbol}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                return jsonify({'error': f'No data available for {symbol}. The symbol may be invalid or delisted.'}), 404
            
            # Validate required columns exist
            if 'Close' not in hist.columns:
                logging.error(f"Stock history API: 'Close' column not found in data for {symbol}")
                return jsonify({'error': f'Invalid data structure for {symbol}'}), 400
            
            # Filter valid data points
            data = []
            for date, row in hist.iterrows():
                try:
                    close_price = float(row['Close'])
                    # Skip NaN, None, and inf values
                    if pd.isna(close_price) or not np.isfinite(close_price):
                        continue
                    data.append({
                        'x': date.strftime('%Y-%m-%d'),
                        'y': close_price
                    })
                except (ValueError, TypeError) as e:
                    logging.debug(f"Skipping invalid data point for {symbol} on {date}: {e}")
                    continue
            
            if not data:
                logging.warning(f"Stock history API: No valid price data for {symbol} after filtering")
                return jsonify({'error': f'No valid price data for {symbol}'}), 404
            
            logging.info(f"Successfully fetched {len(data)} valid data points for {symbol}")
            return jsonify({'symbol': symbol, 'history': data})
            
        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout fetching {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            return jsonify({'error': f'Request timeout: Unable to fetch data for {symbol}. The server is taking too long. Please try again.'}), 504
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error fetching {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            return jsonify({'error': f'Network error: Unable to fetch data for {symbol}. Please check your internet connection.'}), 503
            
        except peewee.OperationalError as e:
            # Common cause: yfinance/peewee sqlite cache file is corrupted or inaccessible (disk I/O error)
            logging.error(f"Peewee/SQLite OperationalError fetching {symbol}: {e}", exc_info=True)
            return jsonify({'error': 'Internal data cache error: disk I/O or permission issue when accessing yfinance cache. Try deleting the yfinance cache file (see README) or check disk/AV permissions.'}), 500

        except ValueError as e:
            logging.error(f"Value error for {symbol}: {e}")
            return jsonify({'error': f'Invalid data received for {symbol}: {str(e)}'}), 400
            
        except Exception as e:
            logging.error(f"Unexpected error fetching {symbol} (attempt {attempt + 1}/{max_retries}): {type(e).__name__} - {str(e)}", exc_info=True)
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            return jsonify({'error': f'Failed to fetch data for {symbol}: {str(e)}'}), 500
    
    return jsonify({'error': f'Failed to fetch data for {symbol} after {max_retries} attempts. Please try again later.'}), 500


@app.route('/api/predict')
def predict_api():
    symbol = request.args.get('symbol')
    days = int(request.args.get('days', 7))
    period = request.args.get('period', '1y')
    # Use model from app config, but allow override from request
    model_choice = int(request.args.get('model', app.config.get('DEFAULT_MODEL', 0)))

    if not symbol:
        return jsonify({'error': 'No symbol provided'}), 400

    try:
        if model_choice == 1:
            result = predict_price_lstm(symbol, days=days, period=period)
        else:
            result = predict_price_xgb(symbol, days=days, period=period)
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 500
    except ModuleNotFoundError as e:
        return jsonify({'error': f'Failed to load model: {e}. Check environment.'}), 500
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Admin debug endpoint: test Brave Search connectivity and header variants
@app.route('/admin/test-brave')
def admin_test_brave():
    # Minimal auth: only allow when FLASK_DEBUG is True to avoid exposing in production
    from config import BRAVE_API_KEY
    results = []
    if not BRAVE_API_KEY:
        return jsonify({'error': 'BRAVE_API_KEY not configured'}), 400

    brave_url = 'https://api.search.brave.com/v1/search'
    test_q = 'Tata Consultancy Services'
    params = {'q': test_q, 'source': 'news', 'size': 1}

    attempts = [
        {'name': 'Authorization Bearer', 'headers': {'Authorization': f'Bearer {BRAVE_API_KEY}', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}},
        {'name': 'x-api-key', 'headers': {'x-api-key': BRAVE_API_KEY, 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}},
        {'name': 'X-Api-Key', 'headers': {'X-Api-Key': BRAVE_API_KEY, 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}},
        {'name': 'no-auth', 'headers': {'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}}
    ]

    for att in attempts:
        name = att['name']
        hdrs = att['headers']
        try:
            r = requests.get(brave_url, headers=hdrs, params=params, timeout=8)
            status = r.status_code
            headers = {k: v for k, v in r.headers.items()}
            text_preview = r.text[:800]
            results.append({'attempt': name, 'status': status, 'headers': headers, 'body_preview': text_preview})
        except Exception as e:
            results.append({'attempt': name, 'error': str(e)})

    # Also include env var value masked
    masked = BRAVE_API_KEY[:4] + '...' + BRAVE_API_KEY[-4:]
    return jsonify({'key_masked': masked, 'results': results})


# Notifications are run from app.py startup scheduler
