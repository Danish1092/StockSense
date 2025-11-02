from flask import render_template, jsonify, request, redirect, url_for, session, flash
import yfinance as yf
import requests
from app import app
from market_data import get_market_movers_cached, format_number_wrapper
from datetime import datetime
import logging
from auth import handle_login, handle_signup_request, handle_signup_otp


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
            if handle_login(email, password):
                session['user_email'] = email
                return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

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
