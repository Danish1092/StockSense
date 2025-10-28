from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from auth import login_required, handle_login, handle_signup
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Import market data functions
from market_data import get_market_movers_cached, format_number_wrapper

# Basic routes
@app.route('/')
def index():
    try:
        gainers, losers = get_market_movers_cached(limit=10)  # Get top 10 gainers and losers from cache
        return render_template('index.html', 
                             gainers=gainers, 
                             losers=losers, 
                             format_number=format_number_wrapper)
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return render_template('index.html', gainers=[], losers=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email and password:
            if handle_login(email, password):
                session['user_email'] = email
                return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        if email and password and username:
            if handle_signup(email, password, username):
                flash('Account created successfully!')
                return redirect(url_for('login'))
        flash('Registration failed')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Market data routes
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

@app.route('/stocks')
def stocks():
    return render_template('stocks.html')

@app.route('/top-gainers')
def top_gainers():
    return render_template('top_gainers.html')

@app.route('/top-losers')
def top_losers():
    return render_template('top_losers.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
