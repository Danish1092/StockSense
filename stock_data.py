import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Tuple

def get_screener_data() -> Tuple[List[Dict], List[Dict]]:
    """Fetch data from Screener.in"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    gainers = []
    losers = []
    
    try:
        # Top Gainers
        url = "https://www.screener.in/screens/666/nse-top-gainers/"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.select('table.data-table tbody tr')
            
            for row in rows[:10]:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    gainers.append({
                        'symbol': cols[0].text.strip(),
                        'name': cols[1].text.strip(),
                        'price': float(cols[2].text.replace('₹', '').replace(',', '').strip()),
                        'change_percent': float(cols[3].text.replace('%', '').strip()),
                        'volume': int(cols[4].text.replace(',', '').strip()),
                        'source': 'Screener.in'
                    })
        
        # Top Losers
        url = "https://www.screener.in/screens/667/nse-top-losers/"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.select('table.data-table tbody tr')
            
            for row in rows[:10]:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    losers.append({
                        'symbol': cols[0].text.strip(),
                        'name': cols[1].text.strip(),
                        'price': float(cols[2].text.replace('₹', '').replace(',', '').strip()),
                        'change_percent': float(cols[3].text.replace('%', '').strip()),
                        'volume': int(cols[4].text.replace(',', '').strip()),
                        'source': 'Screener.in'
                    })
                    
    except Exception as e:
        print(f"Error fetching Screener.in data: {str(e)}")
    
    return gainers, losers

def get_moneycontrol_data() -> Tuple[List[Dict], List[Dict]]:
    """Fetch data from MoneyControl"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    gainers = []
    losers = []
    
    try:
        # Top Gainers
        url = "https://www.moneycontrol.com/stocks/marketstats/nsegainer/index.php"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.select('div.bsr_table table tbody tr')
            
            for row in rows[:10]:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    gainers.append({
                        'symbol': cols[0].text.strip(),
                        'name': cols[1].text.strip(),
                        'price': float(cols[3].text.replace(',', '').strip()),
                        'change': float(cols[4].text.replace(',', '').strip()),
                        'change_percent': float(cols[5].text.replace('%', '').strip()),
                        'volume': int(cols[6].text.replace(',', '').strip()),
                        'source': 'MoneyControl'
                    })
        
        # Top Losers
        url = "https://www.moneycontrol.com/stocks/marketstats/nseloser/index.php"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.select('div.bsr_table table tbody tr')
            
            for row in rows[:10]:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    losers.append({
                        'symbol': cols[0].text.strip(),
                        'name': cols[1].text.strip(),
                        'price': float(cols[3].text.replace(',', '').strip()),
                        'change': float(cols[4].text.replace(',', '').strip()),
                        'change_percent': float(cols[5].text.replace('%', '').strip()),
                        'volume': int(cols[6].text.replace(',', '').strip()),
                        'source': 'MoneyControl'
                    })
    
    except Exception as e:
        print(f"Error fetching MoneyControl data: {str(e)}")
    
    return gainers, losers

def get_market_movers(limit: int = 10) -> Tuple[List[Dict], List[Dict]]:
    """Get top gainers and losers from multiple sources"""
    all_gainers = []
    all_losers = []
    
    # Get data from Screener.in
    screener_gainers, screener_losers = get_screener_data()
    all_gainers.extend(screener_gainers)
    all_losers.extend(screener_losers)
    
    # Add delay between requests
    time.sleep(1)
    
    # Get data from MoneyControl
    mc_gainers, mc_losers = get_moneycontrol_data()
    all_gainers.extend(mc_gainers)
    all_losers.extend(mc_losers)
    
    # Sort by change percentage
    all_gainers.sort(key=lambda x: x['change_percent'], reverse=True)
    all_losers.sort(key=lambda x: x['change_percent'])
    
    # Remove duplicates while preserving order
    def get_unique_stocks(stocks):
        seen = set()
        unique_stocks = []
        for stock in stocks:
            if stock['symbol'] not in seen:
                seen.add(stock['symbol'])
                unique_stocks.append(stock)
        return unique_stocks[:limit]
    
    unique_gainers = get_unique_stocks(all_gainers)
    unique_losers = get_unique_stocks(all_losers)
    
    return unique_gainers, unique_losers

def format_large_number(num: float) -> str:
    """Format large numbers into K, M, B format"""
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T'][magnitude])