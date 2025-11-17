from flask import jsonify
import yfinance as yf

# ...existing code...




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
from config import NEWS_API_KEY

@app.route('/about')
def about():
    return render_template('about.html')
# Predict and Info routes
@app.route('/predict')
def predict():
    # Placeholder: update this list with your 10 company names later
    companies = [
        'TCS.NS', 'RELIANCE.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
        'SBIN.NS', 'ITC.NS', 'LT.NS', 'AXISBANK.NS', 'BHARTIARTL.NS'
    ]
    return render_template('predict.html', companies=companies)

@app.route('/info')
def info():
    company = request.args.get('company')
    if not company:
        return redirect(url_for('predict'))
    # In the future, fetch real data for the company here
    return render_template('info.html', company_name=company)


# Home page with market movers
@app.route('/')
def index():
    try:
        gainers, losers = get_market_movers_cached(limit=10)
        return render_template('index.html', gainers=gainers, losers=losers, format_number=format_number_wrapper)
    except Exception as e:
        logging.error(f"Error fetching market data: {e}")
        return render_template('index.html', gainers=[], losers=[])

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
    symbol = request.args.get('symbol')
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
