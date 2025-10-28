from typing import List, Dict, Tuple
from stock_data import get_market_movers, format_large_number
import time

# Cache for market data to prevent too frequent requests
_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 300  # Cache duration in seconds (5 minutes)
}

def get_market_movers_cached(limit: int = 10) -> Tuple[List[Dict], List[Dict]]:
    """Get cached market movers data, refresh if cache is expired"""
    global _cache
    
    current_time = time.time()
    if _cache['data'] is None or (current_time - _cache['timestamp']) > _cache['cache_duration']:
        try:
            # Cache is empty or expired, fetch new data
            gainers, losers = get_market_movers(limit)
            if gainers and losers:  # Only update cache if we got valid data
                _cache['data'] = (gainers, losers)
                _cache['timestamp'] = current_time
                print(f"Market data refreshed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error refreshing market data: {str(e)}")
            if _cache['data'] is None:  # If no cached data available, return empty lists
                return [], []
    
    return _cache['data']

def format_number_wrapper(num: float) -> str:
    """Wrapper for format_large_number from stock_data"""
    return format_large_number(num)