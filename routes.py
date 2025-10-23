from flask import render_template, jsonify, request, send_from_directory
import yfinance as yf
import requests
from app import app

@app.route('/')
def index():
    return render_template('index.html', title="StockSense - Home")

@app.route('/research')
def research_page():
    return render_template('research/index.html', title="Research - StockSense")

@app.route('/research/reports')
def research_reports():
    return render_template('research/reports.html', title="Reports - StockSense")

@app.route('/research/yearbooks')
def research_yearbooks():
    return render_template('research/yearbooks.html', title="Yearbooks - StockSense")

@app.route('/research/wallchart')
def research_wallchart():
    return render_template('research/wallchart.html', title="Wallchart - StockSense")

@app.route('/demat-account')
def demat_account():
    return render_template('demat_guide.html', title="Demat Account Guide - StockSense")

@app.route('/top-gainers')
def top_gainers_page():
    gainers, _ = fetch_nse_data()
    return render_template('screener/top_gainers.html', gainers=gainers, title="Top Gainers - StockSense")

@app.route('/top-losers')
def top_losers_page():
    _, losers = fetch_nse_data()
    return render_template('screener/top_losers.html', losers=losers, title="Top Losers - StockSense")

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

@app.route('/api/stock/<symbol>')
def stock_details(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    return jsonify(info)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/favicon',
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

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

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', 
        title="404 Not Found - StockSense"
    ), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html',
        title="500 Server Error - StockSense"
    ), 500

@app.route('/stocks')
def stocks():
    return render_template('stocks.html')

@app.route('/about')
def about():
    return render_template('about.html')
