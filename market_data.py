import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
from typing import List, Dict, Tuple

def get_nifty500_symbols() -> List[str]:
    """Get list of Nifty 500 symbols"""
    try:
        nifty500_url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(nifty500_url)
        return df['Symbol'].tolist()
    except:
        # Fallback to top 50 stocks if unable to fetch Nifty 500
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", 
                "HDFC", "BHARTIARTL", "ITC", "KOTAKBANK", "SBIN", "BAJFINANCE", 
                "ASIANPAINT", "WIPRO", "MARUTI", "AXISBANK", "HCLTECH", "ULTRACEMCO"]

def get_stock_data(symbol: str) -> Dict:
    """Get real-time stock data for a single symbol"""
    try:
        stock = yf.Ticker(f"{symbol}.NS")
        info = stock.info
        hist = stock.history(period="1d")
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[0]
        change = current_price - open_price
        change_percent = (change / open_price) * 100
        
        return {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'price': round(current_price, 2),
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'volume': info.get('volume', 0),
            'market_cap': info.get('marketCap', 0),
            'high': round(hist['High'].max(), 2),
            'low': round(hist['Low'].min(), 2)
        }
    except:
        return None

def get_market_movers(limit: int = 10) -> Tuple[List[Dict], List[Dict]]:
    """Get top gainers and losers from the market"""
    symbols = get_nifty500_symbols()
    stock_data = []
    
    # Get data for all stocks
    for symbol in symbols:
        data = get_stock_data(symbol)
        if data:
            stock_data.append(data)
    
    # Sort by change percentage
    stock_data.sort(key=lambda x: x['change_percent'], reverse=True)
    
    # Get top gainers and losers
    gainers = stock_data[:limit]
    losers = stock_data[-limit:]
    losers.reverse()  # Show biggest losers first
    
    return gainers, losers

def format_large_number(num: float) -> str:
    """Format large numbers into K, M, B format"""
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T'][magnitude])