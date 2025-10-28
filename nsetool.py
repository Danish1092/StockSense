"""
Fetch real-time top gainers and losers from multiple financial websites.

Requirements:
    pip install requests beautifulsoup4

Usage:
    python nsetool.py
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import List, Dict, Tuple
import time

def get_moneycontrol_data() -> Tuple[List[Dict], List[Dict]]:
    """Fetch top gainers and losers from MoneyControl"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    }
    
    gainers = []
    losers = []
    
    try:
        # Fetch top gainers
        gainers_url = "https://www.moneycontrol.com/stocks/marketstats/nsegainer/index.php"
        response = requests.get(gainers_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            gainer_rows = soup.select("div.bsr_table.hist_tbl_hm > table > tbody > tr")
            
            for row in gainer_rows[:10]:  # Get top 10 gainers
                cells = row.find_all('td')
                if len(cells) >= 7:
                    gainers.append({
                        'symbol': cells[0].text.strip(),
                        'name': cells[0].text.strip(),
                        'price': float(cells[3].text.replace(',', '').strip()),
                        'change': float(cells[4].text.replace(',', '').strip()),
                        'change_percent': float(cells[5].text.strip().replace('%', '')),
                        'volume': int(cells[6].text.replace(',', '').strip())
                    })
        
        # Fetch top losers
        losers_url = "https://www.moneycontrol.com/stocks/marketstats/nseloser/index.php"
        response = requests.get(losers_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            loser_rows = soup.select("div.bsr_table.hist_tbl_hm > table > tbody > tr")
            
            for row in loser_rows[:10]:  # Get top 10 losers
                cells = row.find_all('td')
                if len(cells) >= 7:
                    losers.append({
                        'symbol': cells[0].text.strip(),
                        'name': cells[0].text.strip(),
                        'price': float(cells[3].text.replace(',', '').strip()),
                        'change': float(cells[4].text.replace(',', '').strip()),
                        'change_percent': float(cells[5].text.strip().replace('%', '')),
                        'volume': int(cells[6].text.replace(',', '').strip())
                    })
                    
    except Exception as e:
        print(f"Error fetching MoneyControl data: {str(e)}")
    
    return gainers, losers


def get_investing_data() -> Tuple[List[Dict], List[Dict]]:
    """Fetch top gainers and losers from Investing.com"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    }
    
    gainers = []
    losers = []
    
    try:
        # Fetch top gainers
        url = "https://in.investing.com/equities/top-stock-gainers"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Process gainers
            gainer_rows = soup.select("table.common-table.js-top-instruments > tbody > tr")
            for row in gainer_rows[:10]:
                cells = row.find_all('td')
                if len(cells) >= 6:
                    gainers.append({
                        'symbol': cells[1].text.strip(),
                        'name': cells[1].text.strip(),
                        'price': float(cells[2].text.replace(',', '').strip()),
                        'change': float(cells[3].text.replace(',', '').strip()),
                        'change_percent': float(cells[4].text.strip().replace('%', '')),
                        'volume': int(cells[5].text.replace(',', '').replace('K', '000').replace('M', '000000').strip())
                    })
        
        # Fetch losers
        url = "https://in.investing.com/equities/top-stock-losers"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Process losers
            loser_rows = soup.select("table.common-table.js-top-instruments > tbody > tr")
            for row in loser_rows[:10]:
                cells = row.find_all('td')
                if len(cells) >= 6:
                    losers.append({
                        'symbol': cells[1].text.strip(),
                        'name': cells[1].text.strip(),
                        'price': float(cells[2].text.replace(',', '').strip()),
                        'change': float(cells[3].text.replace(',', '').strip()),
                        'change_percent': float(cells[4].text.strip().replace('%', '')),
                        'volume': int(cells[5].text.replace(',', '').replace('K', '000').replace('M', '000000').strip())
                    })
                    
    except Exception as e:
        print(f"Error fetching Investing.com data: {str(e)}")
    
    return gainers, losers


def get_screener_data() -> Tuple[List[Dict], List[Dict]]:
    """Fetch top gainers and losers from Screener.in"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    }
    
    gainers = []
    losers = []
    
    try:
        # Fetch data from Screener.in
        url = "https://www.screener.in/screens/gainers-losers/"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Process gainers
            gainer_table = soup.find('div', {'id': 'top-gainers'})
            if gainer_table:
                gainer_rows = gainer_table.select('tr')[1:]  # Skip header row
                for row in gainer_rows[:10]:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        gainers.append({
                            'symbol': cells[0].text.strip(),
                            'name': cells[1].text.strip(),
                            'price': float(cells[2].text.replace(',', '').strip()),
                            'change': float(cells[3].text.replace(',', '').strip()),
                            'change_percent': float(cells[4].text.strip().replace('%', '')),
                            'volume': int(cells[5].text.replace(',', '').strip() if len(cells) > 5 else 0)
                        })
            
            # Process losers
            loser_table = soup.find('div', {'id': 'top-losers'})
            if loser_table:
                loser_rows = loser_table.select('tr')[1:]  # Skip header row
                for row in loser_rows[:10]:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        losers.append({
                            'symbol': cells[0].text.strip(),
                            'name': cells[1].text.strip(),
                            'price': float(cells[2].text.replace(',', '').strip()),
                            'change': float(cells[3].text.replace(',', '').strip()),
                            'change_percent': float(cells[4].text.strip().replace('%', '')),
                            'volume': int(cells[5].text.replace(',', '').strip() if len(cells) > 5 else 0)
                        })
                    
    except Exception as e:
        print(f"Error fetching Screener.in data: {str(e)}")
    
    return gainers, losers

def get_market_movers() -> Tuple[List[Dict], List[Dict]]:
    """Get top gainers and losers from multiple sources and combine them"""
    all_gainers = []
    all_losers = []
    
    # Get data from MoneyControl
    mc_gainers, mc_losers = get_moneycontrol_data()
    all_gainers.extend(mc_gainers)
    all_losers.extend(mc_losers)
    
    # Add small delay before next request
    time.sleep(1)
    
    # Get data from Investing.com
    inv_gainers, inv_losers = get_investing_data()
    all_gainers.extend(inv_gainers)
    all_losers.extend(inv_losers)
    
    # Add small delay before next request
    time.sleep(1)
    
    # Get data from Screener.in
    scr_gainers, scr_losers = get_screener_data()
    all_gainers.extend(scr_gainers)
    all_losers.extend(scr_losers)
    
    # Sort and get unique entries based on change percentage
    all_gainers.sort(key=lambda x: x['change_percent'], reverse=True)
    all_losers.sort(key=lambda x: x['change_percent'])
    
    # Get top 10 unique gainers and losers
    unique_gainers = []
    unique_losers = []
    seen_symbols = set()
    
    for gainer in all_gainers:
        if gainer['symbol'] not in seen_symbols and len(unique_gainers) < 10:
            unique_gainers.append(gainer)
            seen_symbols.add(gainer['symbol'])
    
    seen_symbols.clear()
    for loser in all_losers:
        if loser['symbol'] not in seen_symbols and len(unique_losers) < 10:
            unique_losers.append(loser)
            seen_symbols.add(loser['symbol'])
    
    return unique_gainers, unique_losers


def format_large_number(num: float) -> str:
    """Format large numbers into K, M, B format"""
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T'][magnitude])

if __name__ == "__main__":
    # Get real-time data from multiple sources
    gainers, losers = get_market_movers()
    
    # Print timestamp and results
    print(f"\nMarket Movers (fetched {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("\nTop Gainers:")
    for i, stock in enumerate(gainers, 1):
        print(f"{i}. {stock['name']} ({stock['symbol']})")
        print(f"   Price: ₹{stock['price']:.2f} | Change: {stock['change_percent']:+.2f}% | Volume: {format_large_number(stock['volume'])}")
    
    print("\nTop Losers:")
    for i, stock in enumerate(losers, 1):
        print(f"{i}. {stock['name']} ({stock['symbol']})")
        print(f"   Price: ₹{stock['price']:.2f} | Change: {stock['change_percent']:+.2f}% | Volume: {format_large_number(stock['volume'])}")
