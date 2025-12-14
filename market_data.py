from typing import List, Dict, Tuple
from stock_data import get_market_movers, format_large_number
import time
import logging

# Cache for market data to prevent too frequent requests
_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 300  # Cache duration in seconds (5 minutes)
}


def get_market_movers_cached(limit: int = 10) -> Tuple[List[Dict], List[Dict]]:
    """Get cached market movers data, refresh if cache is expired.

    Always return a tuple of two lists (gainers, losers). If fresh data cannot
    be fetched and no cache exists, return two empty lists instead of None.
    """
    global _cache

    current_time = time.time()
    if _cache['data'] is None or (current_time - _cache['timestamp']) > _cache['cache_duration']:
        try:
            # Cache is empty or expired, fetch new data
            gainers, losers = get_market_movers(limit)
            if gainers is not None and losers is not None:
                _cache['data'] = (gainers, losers)
                _cache['timestamp'] = current_time
                logging.info("Market data refreshed at %s", time.strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as e:
            logging.exception('Error refreshing market data: %s', e)
            # If no cached data available, fall through and return empty lists below

    # Ensure we always return a tuple of lists
    if _cache['data']:
        return _cache['data']
    return [], []

def format_number_wrapper(num: float) -> str:
    """Wrapper for format_large_number from stock_data"""
    return format_large_number(num)