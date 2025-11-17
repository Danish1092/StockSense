# Troubleshooting Guide

## API 500 Errors / Stock History Not Loading

If you see a **500 error** in the browser console when trying to load stock charts:

### Common Causes and Solutions

#### 1. **yfinance Network Timeout**
- **Problem**: yfinance request is taking too long or timing out
- **Solution**: 
  - Check your internet connection
  - Disable VPN temporarily
  - Clear your browser cache
  - Try a different stock symbol to see if it's symbol-specific

#### 2. **Yahoo Finance Server Issues**
- **Problem**: Yahoo Finance servers may be temporarily unavailable or blocking requests
- **Solution**: 
  - Wait a few minutes and try again
  - Check https://status.finance.yahoo.com for any known issues
  - Try accessing https://finance.yahoo.com in your browser to verify connectivity

#### 3. **Invalid Stock Symbol**
- **Problem**: The symbol doesn't exist or is misspelled
- **Solution**: 
  - Verify the stock symbol is correct (e.g., TCS.NS, not TCS.N)
  - Check Yahoo Finance website to confirm the symbol format
  - Ensure you're using the correct exchange suffix (.NS for NSE, .BO for BSE)

#### 4. **Missing Dependencies**
- **Problem**: Required Python packages not installed or outdated
- **Solution**: 
  ```bash
  pip install --upgrade yfinance pandas numpy requests
  ```

#### 5. **Check Server Logs**
- **Problem**: Need to see what's actually failing
- **Solution**: 
  - Look at the Flask server console/terminal for detailed error messages
  - The logs will show the exact exception and traceback

## Graphs Not Showing / yfinance Errors

If you're experiencing issues where stock graphs are not displaying or you see errors like:
- "Failed to get ticker 'TCS.NS' reason: Expecting value: line 1 column 1"
- "No timezone found, symbol may be delisted"
- "Empty history returned from yfinance"

### Common Causes and Solutions

#### 1. **Network/Firewall Issues**
- **Problem**: Your network or firewall may be blocking requests to Yahoo Finance servers
- **Solution**: 
  - Check if you can access https://finance.yahoo.com in your browser
  - If using a corporate network, ask your IT department to whitelist Yahoo Finance domains
  - Try using a different network (mobile hotspot, home network, etc.)
  - Disable VPN temporarily to test if it's blocking the connection

#### 2. **Outdated yfinance Package**
- **Problem**: An outdated version of yfinance may have compatibility issues
- **Solution**: Update yfinance to the latest version
  ```bash
  pip install --upgrade yfinance
  ```

#### 3. **Rate Limiting**
- **Problem**: Yahoo Finance may rate-limit requests if too many are made in a short time
- **Solution**: 
  - Wait a few minutes before trying again
  - The app now includes automatic retry logic with exponential backoff
  - Clear browser cache and cookies

#### 4. **Invalid Stock Symbol**
- **Problem**: The stock symbol might be incorrect or the stock may be delisted
- **Solution**: 
  - Verify the symbol on Yahoo Finance website
  - Ensure you're using the correct exchange suffix (e.g., .NS for NSE, .BO for BSE)
  - Try a different stock symbol to see if the issue persists

#### 5. **Python Package Conflicts**
- **Problem**: Conflicting package versions may cause issues
- **Solution**: Create a fresh virtual environment
  ```bash
  # Create new virtual environment
  python -m venv venv_new
  
  # Activate it
  # On Windows:
  venv_new\Scripts\activate
  # On Linux/Mac:
  source venv_new/bin/activate
  
  # Install requirements
  pip install -r requirements.txt
  ```

#### 6. **SSL/Certificate Issues**
- **Problem**: SSL certificate verification failures
- **Solution**: 
  - Update certificates: `pip install --upgrade certifi`
  - If the issue persists, temporarily disable SSL verification (not recommended for production)

### Recent Improvements

The application now includes:
- **Automatic retry logic**: Failed requests are automatically retried up to 3 times with exponential backoff
- **Better error messages**: More descriptive error messages to help identify the issue
- **Proper headers**: HTTP requests now include proper User-Agent headers to avoid being blocked
- **Timeout handling**: Requests now have a 10-second timeout to prevent hanging
- **Enhanced logging**: Detailed logs help track down issues

### Checking Logs

Look at your terminal/console output for detailed error messages. The logs will indicate:
- Network errors
- Empty data responses
- Retry attempts
- Successful data fetches

### Testing yfinance Directly

To test if yfinance is working on your system:

```python
import yfinance as yf
ticker = yf.Ticker("TCS.NS")
hist = ticker.history(period="1mo")
print(hist)
```

If this fails, the issue is with yfinance connectivity, not the application.

### Still Having Issues?

1. Check the requirements.txt and ensure all dependencies are installed
2. Make sure you're using Python 3.8 or higher
3. Try accessing the API endpoint directly: `http://127.0.0.1:5000/api/stock-history?symbol=TCS.NS&period=1mo`
4. Check if antivirus software is blocking the connection
5. Restart the Flask application

### Contact

If none of these solutions work, please provide:
- Your Python version
- Your yfinance version (`pip show yfinance`)
- Complete error message from terminal
- Your network configuration (corporate/home/VPN)
