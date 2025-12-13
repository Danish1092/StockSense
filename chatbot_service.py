"""
Chatbot Service - Integrates Brave Search and OpenAI ChatGPT
Handles knowledge enrichment from Brave Search before querying ChatGPT
"""

import logging
import re
import requests
import yfinance as yf
from datetime import datetime
from typing import Optional, List, Dict
from config import BRAVE_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)


def brave_search(query: str, size: int = 4, timeout: int = 8) -> List[Dict]:
    """
    Perform a Brave Search query and return simplified results.
    
    Args:
        query: Search query string
        size: Number of results to return
        timeout: Request timeout in seconds
    
    Returns:
        List of dicts with keys: 'title', 'url', 'snippet'
    """
    results = []
    if not BRAVE_API_KEY:
        logger.warning("BRAVE_API_KEY not configured")
        return results

    # Multiple endpoint variants for robustness
    endpoints = [
        'https://api.search.brave.com/v1/search',
        'https://api.search.brave.com/res/v1/web/search'
    ]
    header_variants = [
        ('X-Subscription-Token', BRAVE_API_KEY),
        ('x-api-key', BRAVE_API_KEY)
    ]

    for endpoint in endpoints:
        for hname, hval in header_variants:
            try:
                params = {'q': query, 'size': size, 'source': 'news'}
                headers = {
                    hname: hval,
                    'Accept': 'application/json',
                    'User-Agent': 'StockSense/1.0'
                }
                
                logger.info(f'Brave Search - endpoint: {endpoint}, header: {hname}, query: {query}')
                r = requests.get(endpoint, headers=headers, params=params, timeout=timeout)
                
                if r.status_code == 403:
                    logger.warning(f'Brave returned 403 with header {hname} at {endpoint}')
                    continue
                
                if r.status_code != 200:
                    logger.warning(f'Brave returned {r.status_code}')
                    continue
                
                try:
                    data = r.json() or {}
                except Exception as e:
                    logger.warning(f'Brave returned non-JSON response: {e}')
                    continue
                
                # Parse results based on response structure
                if 'results' in data:
                    for item in data.get('results', []):
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'snippet': item.get('description', '')
                        })
                elif 'web' in data and isinstance(data['web'], dict):
                    for item in data['web'].get('results', []):
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'snippet': item.get('snippet', '')
                        })
                
                if results:
                    logger.info(f'Brave Search successful: {len(results)} results found')
                    return results[:size]
            
            except requests.exceptions.Timeout:
                logger.warning(f'Brave request timeout at {endpoint}')
                continue
            except Exception as e:
                logger.warning(f'Brave request failed: {e}')
                continue

    logger.info('Brave Search: No results found from any endpoint')
    return results


def should_enrich_with_brave(user_query: str) -> bool:
    """
    Determine if the user query should be enriched with Brave Search.
    
    Triggers include financial metrics, recent data, filings, etc.
    """
    if not BRAVE_API_KEY:
        return False
    
    lower_query = user_query.lower()
    
    # Keywords that indicate need for current/external knowledge
    finance_triggers = [
        'profit', 'net profit', 'pat', 'earnings', 'revenue',
        'fy', 'fiscal', 'annual report', 'filing', 'results',
        'quarter', 'q1', 'q2', 'q3', 'q4', 'fy202', 'fy20',
        'turnover', 'ebitda', 'dividend', 'eps', 'loss',
        'debt', 'cash', 'assets', 'liabilities', 'balance sheet',
        'financial', 'accounts', 'consolidated', 'standalone',
        '2024', '2025', '2026'
    ]
    
    # Check for financial triggers
    if any(trigger in lower_query for trigger in finance_triggers):
        return True
    
    # Check for explicit year/FY patterns
    if re.search(r"\b(20\d{2})(?:[-/–—](20\d{2}|\d{2}))?\b", lower_query):
        return True
    
    if re.search(r"\bfy\s*\d{2,4}\b", lower_query):
        return True
    
    return False


def get_stock_history_context(symbol: str, period: str = '1mo') -> str:
    """
    Fetch recent stock price history for context.
    
    Args:
        symbol: Stock ticker (e.g., 'TCS.NS')
        period: History period (1mo, 3mo, 1y, max, etc.)
    
    Returns:
        Formatted context string with recent price data
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, timeout=15)
        
        if hist is None or hist.empty or 'Close' not in hist.columns:
            return ""
        
        # Get last 14 closes
        recent_points = []
        for date, row in hist.tail(14).iterrows():
            try:
                close_price = float(row['Close'])
                recent_points.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'close': close_price
                })
            except Exception:
                continue
        
        if not recent_points:
            return ""
        
        first = recent_points[0]['close']
        last = recent_points[-1]['close']
        pct_change = ((last - first) / first * 100) if first != 0 else 0.0
        
        dates_prices = ', '.join([f"{p['date']}:{p['close']:.2f}" for p in recent_points])
        
        context = (
            f"Recent price data ({len(recent_points)} days, period={period}): "
            f"last_close={last:.2f}, change={pct_change:.2f}%. "
            f"Recent closes: [{dates_prices}]"
        )
        
        return context
    
    except Exception as e:
        logger.debug(f'Could not fetch stock history: {e}')
        return ""


def query_chatgpt_with_brave(
    user_message: str,
    company_name: str = "",
    symbol: str = "",
    period: str = "1mo",
    conversation_history: Optional[List[Dict]] = None
) -> Dict:
    """
    Query ChatGPT with Brave Search enrichment.
    
    Workflow:
    1. Check if user query should be enriched with Brave Search
    2. If yes, fetch Brave Search results
    3. Pass Brave context + stock history to ChatGPT system prompt
    4. Return ChatGPT response with sources
    
    Args:
        user_message: The user's question
        company_name: Name of the company being discussed
        symbol: Stock ticker symbol
        period: Price history period
        conversation_history: Previous messages for context
    
    Returns:
        Dictionary with:
        - success: bool
        - response: str (ChatGPT response text)
        - brave_context: str (sources used, if any)
        - error: str (error message if failed)
    """
    if not OPENAI_API_KEY:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        # Determine if Brave Search is needed
        enrich_query = should_enrich_with_brave(user_message)
        
        brave_context = ""
        brave_sources = []
        
        # Fetch Brave Search results if needed
        if enrich_query:
            search_query = f"{company_name} {user_message}".strip()
            brave_hits = brave_search(search_query, size=4)
            
            if brave_hits:
                for hit in brave_hits:
                    title = hit.get('title', '')
                    snippet = hit.get('snippet', '')
                    url = hit.get('url', '')
                    
                    # Combine title and snippet
                    source_text = (title + ': ' + snippet).strip(': ').strip()
                    
                    if url:
                        source_text += f" (Source: {url})"
                    
                    brave_sources.append(source_text)
                
                if brave_sources:
                    brave_context = "\n\nExternal Knowledge (Brave Search - Latest News & Data):\n" + "\n- ".join(brave_sources)
                    
                    # Keep context reasonably sized
                    if len(brave_context) > 2000:
                        brave_context = brave_context[:1970] + "...\n[Note: More sources available but truncated for length]"
                    
                    logger.info(f'Brave enrichment: {len(brave_sources)} sources for: {company_name}')
        
        # Get stock price history context
        history_context = ""
        if symbol:
            history_context = get_stock_history_context(symbol, period)
        
        # Build system prompt
        base_system = (
            "You are an expert AI assistant specialized in stock market and company financial analysis. "
            "Always respond in English only. Provide informative, accurate, and concise responses. "
            "When referencing external knowledge from Brave Search, clearly cite your sources."
        )
        
        if company_name:
            base_system += f" The user is asking about {company_name}."
        
        # Add stock history context
        if history_context:
            base_system += f"\n\nStock Price Context: {history_context}"
        
        # Add Brave Search context
        if brave_context:
            base_system += brave_context
        
        # Prepare messages
        messages = conversation_history or []
        if not messages or messages[-1].get('role') != 'user':
            messages = messages + [{'role': 'user', 'content': user_message}]
        
        # Prepare OpenAI request
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        body = {
            'model': 'gpt-4o-mini',  # Using newer, more cost-effective model
            'messages': [{'role': 'system', 'content': base_system}] + messages,
            'max_completion_tokens': 1000,
            'temperature': 0.7
        }
        
        logger.info(f'ChatGPT request - company: {company_name}, brave_enriched: {bool(brave_context)}')
        
        # Call OpenAI API
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=body,
            timeout=30
        )
        
        # Handle response
        if response.status_code != 200:
            logger.error(f'OpenAI API error: {response.status_code} - {response.text}')
            return {
                'success': False,
                'error': f'OpenAI API returned {response.status_code}'
            }
        
        try:
            response_json = response.json()
        except Exception as e:
            logger.error(f'Failed to parse OpenAI response: {e}')
            return {
                'success': False,
                'error': 'Failed to parse OpenAI response'
            }
        
        # Extract response text
        assistant_text = ""
        try:
            if 'choices' in response_json and len(response_json['choices']) > 0:
                choice = response_json['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    assistant_text = choice['message']['content'].strip()
        except Exception as e:
            logger.warning(f'Failed to extract assistant text: {e}')
        
        if not assistant_text:
            return {
                'success': False,
                'error': 'No response from ChatGPT'
            }
        
        return {
            'success': True,
            'response': assistant_text,
            'brave_context': brave_context if brave_context else None,
            'sources_count': len(brave_sources) if brave_sources else 0
        }
    
    except requests.exceptions.Timeout:
        logger.error('OpenAI request timeout')
        return {
            'success': False,
            'error': 'Request timeout while contacting OpenAI'
        }
    except Exception as e:
        logger.error(f'Unexpected error in query_chatgpt_with_brave: {e}', exc_info=True)
        return {
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }
