from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import json
import pandas as pd
import yfinance as yf

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)

# Add market indices data
market_indices = {
    'NIFTY': {'value': '18,500', 'change': '+0.5%', 'color': 'green'},
    'SENSEX': {'value': '62,300', 'change': '+0.4%', 'color': 'green'},
    'NSE': {'value': '', 'change': '-0.2%', 'color': 'red'},
    'BSE': {'value': '', 'change': '+0.3%', 'color': 'green'}
}

# Update bundles with all categories from index.html
bundles = {
    'efficient_banks': {
        'title': 'Efficient Banks',
        'description': 'Top performing banking stocks with stable growth and consistent dividends',
        'icon': 'bank',
        'stocks': [
            {'name': 'HDFC Bank', 'symbol': 'HDFCBANK', 'price': '1680.25'},
            {'name': 'ICICI Bank', 'symbol': 'ICICIBANK', 'price': '985.25'},
            {'name': 'SBI', 'symbol': 'SBIN', 'price': '565.80'}
        ]
    },
    'tech_leaders': {
        'title': 'Tech Leaders',
        'description': 'Top-tier technology companies leading digital innovation',
        'icon': 'tech'
    },
    'green_energy': {
        'title': 'Green Energy',
        'description': 'Sustainable and renewable energy sector investments',
        'icon': 'energy'
    },
    'dividend_kings': {
        'title': 'Dividend Kings',
        'description': 'Companies with consistent dividend growth over decades',
        'icon': 'crown'
    },
    'infrastructure_giants': {
        'title': 'Infrastructure Giants',
        'description': 'Major companies in construction and infrastructure development',
        'icon': 'building'
    }
}

# Reports data (update the URLs to be relative to static folder)
reports = {
    'market_reports': [
        {
            'title': 'Q3 2023 Market Analysis',
            'url': 'reports/Q3_2023.pdf',
            'date': '2023-10-15'
        },
        {
            'title': 'Technology Sector Review',
            'url': 'reports/tech_sector_2023.pdf',
            'date': '2023-11-01'
        }
    ]
}

# Yearbooks data
yearbooks = {
    '2023': {'url': '/static/yearbooks/2023.pdf', 'size': '25MB'},
    '2022': {'url': '/static/yearbooks/2022.pdf', 'size': '23MB'},
    '2021': {'url': '/static/yearbooks/2021.pdf', 'size': '22MB'}
}

# Sample data for top gainers and losers
top_gainers_data = [
    {'name': 'Adani Green', 'symbol': 'ADANIGREEN', 'price': '1580.45', 'change': '+8.5%', 'volume': '2.1M'},
    {'name': 'Tata Motors', 'symbol': 'TATAMOTORS', 'price': '785.30', 'change': '+7.2%', 'volume': '5.3M'},
    {'name': 'Bajaj Finance', 'symbol': 'BAJFINANCE', 'price': '6890.75', 'change': '+6.8%', 'volume': '1.8M'},
    {'name': 'HDFC Bank', 'symbol': 'HDFCBANK', 'price': '1680.25', 'change': '+6.5%', 'volume': '3.2M'},
    {'name': 'Reliance', 'symbol': 'RELIANCE', 'price': '2785.50', 'change': '+6.2%', 'volume': '4.5M'},
    {'name': 'TCS', 'symbol': 'TCS', 'price': '3580.75', 'change': '+5.8%', 'volume': '2.7M'}
]

top_losers_data = [
    {'name': 'Tech Mahindra', 'symbol': 'TECHM', 'price': '1120.30', 'change': '-7.5%', 'volume': '3.4M'},
    {'name': 'Wipro', 'symbol': 'WIPRO', 'price': '402.45', 'change': '-6.8%', 'volume': '4.1M'},
    {'name': 'HCL Tech', 'symbol': 'HCLTECH', 'price': '1245.60', 'change': '-6.2%', 'volume': '2.9M'},
    {'name': 'Infosys', 'symbol': 'INFY', 'price': '1489.90', 'change': '-5.8%', 'volume': '3.8M'},
    {'name': 'Sun Pharma', 'symbol': 'SUNPHARMA', 'price': '890.45', 'change': '-5.2%', 'volume': '2.3M'},
    {'name': 'Dr Reddy', 'symbol': 'DRREDDY', 'price': '4567.30', 'change': '-4.8%', 'volume': '1.7M'}
]

# Add super investors data
super_investors = [
    {
        'name': 'Warren Buffett',
        'company': 'Berkshire Hathaway',
        'description': 'Known for value investing and long-term growth strategies',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Warren_Buffett_KU_Visit.jpg/220px-Warren_Buffett_KU_Visit.jpg'
    },
    {
        'name': 'Rakesh Jhunjhunwala',
        'company': 'RARE Enterprises',
        'description': "India's most successful equity investor",
        'image_url': 'https://static.toiimg.com/thumb/msid-93519053,width-400,resizemode-4/93519053.jpg'
    },
    # Add other investors...
]

# Enhanced IPO data
ipo_offerings = {
    'active': {
        'name': 'Jio Financial Services',
        'sector': 'Finance Sector',
        'price_band': {'min': 295, 'max': 340},
        'lot_size': 44,
        'subscription': {
            'QIB': 85,
            'NII': 62,
            'retail': 73
        },
        'close_date': '2023-12-15'
    },
    'upcoming': {
        'name': 'Tata Technologies',
        'sector': 'Technology Sector',
        'expected_price': {'min': 475, 'max': 500},
        'issue_size': 3500,
        'details': {
            'fresh_issue': 2000,
            'offer_for_sale': 1500,
            'listing': ['BSE', 'NSE']
        },
        'expected_date': '2024-01-10'
    }
}

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Get form data
            data = {
                'username': request.form.get('username').strip(),
                'email': request.form.get('email').strip(),
                'password': request.form.get('password')
            }
            
            # Validate data presence
            if not all(data.values()):
                flash('All fields are required')
                return redirect(url_for('signup'))

            # Check existing user with username or email
            existing_user = User.query.filter(
                db.or_(
                    User.username == data['username'],
                    User.email == data['email']
                )
            ).first()

            if existing_user:
                flash('Username or email already exists')
                return redirect(url_for('signup'))

            # Create new user
            new_user = User(
                username=data['username'],
                email=data['email'],
                password=generate_password_hash(data['password'], method='sha256')
            )
            new_user.save_to_db()

            # Log the user in
            session['user_id'] = new_user.id
            flash('Account created successfully!')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username').strip()
            password = request.form.get('password')

            # Find user by username
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                # Update last login time
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Set session
                session['user_id'] = user.id
                session['username'] = user.username
                
                flash('Welcome back, {}!'.format(user.username))
                return redirect(url_for('index'))
            
            flash('Invalid username or password')
            return redirect(url_for('login'))

        except Exception as e:
            flash('An error occurred during login')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('index'))

# Helper function to get current user
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# Add company information for footer
company_info = {
    'name': 'StockSense',
    'description': 'Your trusted partner for intelligent stock market analysis and predictions.',
    'contact': {
        'email': 'support@stocksense.com',
        'phone': '+91 1234567890',
        'location': 'Mumbai, India'
    },
    'social_media': {
        'twitter': 'https://twitter.com/stocksense',
        'linkedin': 'https://linkedin.com/company/stocksense',
        'instagram': 'https://instagram.com/stocksense'
    }
}

@app.route('/')
def index():
    return render_template('index.html', 
        market_indices=market_indices,
        trending_stocks=top_gainers_data[:6],
        bundles=bundles,
        super_investors=super_investors,
        ipo_offerings=ipo_offerings,
        company_info=company_info,
        user=get_current_user()
    )

@app.route('/bundle/<bundle_id>')
def get_bundle(bundle_id):
    if bundle_id in bundles:
        return jsonify(bundles[bundle_id])
    return jsonify({'error': 'Bundle not found'}), 404

@app.route('/reports')
def get_reports():
    return render_template('reports.html', reports=reports['market_reports'])

@app.route('/yearbooks')
def get_yearbooks():
    return render_template('yearbooks.html', yearbooks=yearbooks)

def fetch_nse_data():
    try:
        # NSE API endpoint for stock data
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        
        # Fetch data from NSE
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()['data']
        
        # Process the data
        stocks = []
        for stock in data:
            stocks.append({
                'name': stock['symbol'],
                'symbol': stock['symbol'],
                'price': stock['lastPrice'],
                'change': f"{stock['pChange']}%",
                'volume': f"{int(stock['totalTradedVolume']/1000000)}M"
            })
        
        # Sort by percentage change
        gainers = sorted(stocks, key=lambda x: float(x['change'].strip('%')), reverse=True)[:10]
        losers = sorted(stocks, key=lambda x: float(x['change'].strip('%')))[:10]
        
        return gainers, losers
    except Exception as e:
        print(f"Error fetching data: {e}")
        return [], []

@app.route('/top-gainers')
def top_gainers_view():
    gainers, _ = fetch_nse_data()
    return render_template('top_gainers.html', gainers=gainers)

@app.route('/top-losers')
def top_losers_view():
    _, losers = fetch_nse_data()
    return render_template('top_losers.html', losers=losers)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/favicon',
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/screener/top-gainers')
def top_gainers():
    # Get top gaining stocks using yfinance
    nifty500 = yf.download('^NSEI', period='1d')
    # Process data and sort by gains
    return render_template('screener/top_gainers.html', stocks=top_stocks)

@app.route('/screener/top-losers')
def top_losers():
    # Similar to top gainers but sort by losses
    return render_template('screener/top_losers.html', stocks=bottom_stocks)

@app.route('/research/reports')
def reports_view():
    reports_data = [
        {
            'title': 'Q4 2023 Market Analysis',
            'date': datetime(2023, 12, 1),
            'description': 'Comprehensive analysis of market trends and predictions for Q4 2023',
            'file_path': 'reports/Q4_2023.pdf'
        },
        {
            'title': 'Technology Sector Review 2023',
            'date': datetime(2023, 11, 15),
            'description': 'In-depth analysis of technology sector performance and future outlook',
            'file_path': 'reports/tech_sector_2023.pdf'
        },
        # Add more reports here
    ]
    return render_template('research/reports.html', reports=reports_data)

@app.route('/research/yearbooks')
def yearbooks_view():
    return render_template('research/yearbooks.html')

@app.route('/research/wallchart')
def wallchart():
    return render_template('research/wallchart.html')

@app.route('/api/stock-search')
def stock_search():
    query = request.args.get('q', '')
    stocks = Stock.query.filter(Stock.symbol.like(f'%{query}%')).all()
    return jsonify([s.to_dict() for s in stocks])

@app.route('/api/stock/<symbol>')
def stock_details(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    return jsonify(info)

@app.route('/api/ipo/active')
def active_ipos():
    ipos = IPO.query.filter_by(status='active').all()
    return jsonify([ipo.to_dict() for ipo in ipos])

# Add new routes
@app.route('/api/super-investors')
def get_super_investors():
    return jsonify(super_investors)

@app.route('/api/ipo-offerings')
def get_ipo_offerings():
    return jsonify(ipo_offerings)

@app.route('/api/search-stocks')
def search_stocks():
    query = request.args.get('q', '').upper()
    filtered_stocks = []
    
    if query:
        # Filter from your stock list based on query
        for stock in stocksList:  # Assuming you have stocksList defined
            if query in stock['symbol'] or query in stock['name'].upper():
                filtered_stocks.append(stock)
    
    return jsonify(filtered_stocks)

@app.route('/demat-guide')
def demat_guide():
    guide_data = {
        'required_documents': [
            {'title': 'PAN Card', 'icon': 'document'},
            {'title': 'Aadhaar Card', 'icon': 'id'},
            {'title': 'Bank Statement/Passbook', 'icon': 'bank'},
            {'title': 'Passport Size Photos', 'icon': 'photo'}
        ],
        'process_steps': [
            {'step': 1, 'title': 'Choose a Depository Participant (DP)'},
            {'step': 2, 'title': 'Fill the Account Opening Form'},
            {'step': 3, 'title': 'Submit KYC Documents'},
            {'step': 4, 'title': 'In-Person Verification'}
        ],
        'important_points': [
            {'title': 'Annual Maintenance Charges Apply', 'icon': 'money'},
            {'title': 'Keep Login Credentials Safe', 'icon': 'lock'},
            {'title': 'Link Your Bank Account', 'icon': 'link'},
            {'title': 'Enable Two-Factor Authentication', 'icon': 'shield'}
        ]
    }
    return render_template('demat_guide.html', guide=guide_data)

@app.route('/api/market-indices')
def get_market_indices():
    return jsonify(market_indices)

@app.route('/api/wallchart')
def get_wallchart():
    wallchart_data = {
        'indices': {
            'NIFTY50': {'current': '18500', 'change': '+150', 'volume': '245M'},
            'BANKNIFTY': {'current': '42300', 'change': '+280', 'volume': '180M'},
            'NIFTYIT': {'current': '32100', 'change': '-120', 'volume': '95M'}
        },
        'sectors': [
            {'name': 'Banking', 'performance': '+2.5%', 'trend': 'up'},
            {'name': 'IT', 'performance': '-1.2%', 'trend': 'down'},
            {'name': 'Pharma', 'performance': '+0.8%', 'trend': 'up'}
        ],
        'market_depth': {
            'advances': 1250,
            'declines': 850,
            'unchanged': 120
        }
    }
    return jsonify(wallchart_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
