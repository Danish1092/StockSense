#!/usr/bin/env python
"""
Test script for chatbot integration with Brave Search + ChatGPT.

This script demonstrates the chatbot_service functionality without running the full Flask app.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test imports
try:
    from chatbot_service import (
        brave_search,
        should_enrich_with_brave,
        get_stock_history_context,
        query_chatgpt_with_brave
    )
    print("✓ Successfully imported chatbot_service")
except ImportError as e:
    print(f"✗ Failed to import chatbot_service: {e}")
    sys.exit(1)

def test_should_enrich():
    """Test the enrichment detection logic."""
    print("\n" + "="*60)
    print("TEST 1: Enrichment Detection")
    print("="*60)
    
    test_cases = [
        ("What was the profit of TCS in FY2024-2025?", True, "Financial metric + year"),
        ("Show me Infosys Q3 earnings", True, "Earnings + quarter"),
        ("What is the stock market?", False, "General knowledge"),
        ("Explain blockchain technology", False, "General knowledge"),
        ("HDFC financial results 2024", True, "Financial data + year"),
        ("What's the current price of Reliance?", False, "Price - no specific year"),
    ]
    
    for query, expected, reason in test_cases:
        result = should_enrich_with_brave(query)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{query}'")
        print(f"   → Enrich: {result} (Expected: {expected}) - {reason}")

def test_brave_search():
    """Test Brave Search functionality."""
    print("\n" + "="*60)
    print("TEST 2: Brave Search API")
    print("="*60)
    
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        print("⚠ BRAVE_API_KEY not set - skipping Brave Search test")
        return
    
    print(f"✓ BRAVE_API_KEY is configured")
    
    test_queries = [
        "TCS profit FY2024-2025",
        "Infosys Q3 earnings 2024",
    ]
    
    for query in test_queries:
        print(f"\nSearching: '{query}'")
        try:
            results = brave_search(query, size=3)
            print(f"✓ Got {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['title'][:60]}...")
                if result['snippet']:
                    print(f"     {result['snippet'][:60]}...")
        except Exception as e:
            print(f"✗ Search failed: {e}")

def test_stock_history():
    """Test stock history context."""
    print("\n" + "="*60)
    print("TEST 3: Stock History Context")
    print("="*60)
    
    test_symbols = [
        ("TCS.NS", "1mo"),
        ("RELIANCE.NS", "3mo"),
    ]
    
    for symbol, period in test_symbols:
        print(f"\nFetching: {symbol} ({period})")
        try:
            context = get_stock_history_context(symbol, period)
            if context:
                print(f"✓ Got context:")
                print(f"  {context[:100]}...")
            else:
                print(f"⚠ No context returned")
        except Exception as e:
            print(f"✗ Failed: {e}")

def test_chatgpt_with_brave():
    """Test full chatbot integration."""
    print("\n" + "="*60)
    print("TEST 4: Full Chatbot Integration (ChatGPT + Brave)")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠ OPENAI_API_KEY not set - skipping ChatGPT test")
        return
    
    print(f"✓ OPENAI_API_KEY is configured")
    
    test_query = "What was the profit of TCS in FY2024-2025?"
    print(f"\nQuery: '{test_query}'")
    print("Calling chatbot_service...")
    
    try:
        result = query_chatgpt_with_brave(
            user_message=test_query,
            company_name="TCS",
            symbol="TCS.NS",
            period="1mo"
        )
        
        if result.get('success'):
            print("✓ Success!")
            print(f"  Sources: {result.get('sources_count', 0)}")
            print(f"  Response preview: {result.get('response', '')[:100]}...")
        else:
            print(f"✗ Failed: {result.get('error')}")
    except Exception as e:
        print(f"✗ Exception: {e}")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CHATBOT INTEGRATION TEST SUITE")
    print("="*60)
    
    # Test 1: Enrichment detection (doesn't need API keys)
    test_should_enrich()
    
    # Test 2: Brave Search (needs BRAVE_API_KEY)
    test_brave_search()
    
    # Test 3: Stock history (needs yfinance)
    test_stock_history()
    
    # Test 4: Full integration (needs both API keys)
    test_chatgpt_with_brave()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
    print("\nNext Steps:")
    print("1. Ensure BRAVE_API_KEY and OPENAI_API_KEY are in .env")
    print("2. Run: python app.py")
    print("3. Open http://localhost:5000 and test the chatbot")
    print("\nKey Features:")
    print("✓ Automatic Brave Search enrichment for financial queries")
    print("✓ Real-time stock price context")
    print("✓ Source attribution in responses")
    print("✓ Conversation history support")

if __name__ == "__main__":
    main()
