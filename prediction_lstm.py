import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, Any
import os
import joblib

def _get_features_df(symbol: str, period: str = '1y') -> pd.DataFrame:
    """Fetch yfinance history and calculate all features required by the model."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period)
    if df.empty:
        raise ValueError(f'No historical data from yfinance for symbol {symbol}')

    # Calculate all indicators, preserving yfinance column names
    df['Daily_Return'] = df['Close'].pct_change()
    df['Log_Return'] = np.log1p(df['Daily_Return'])
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['Volatility'] = df['Daily_Return'].rolling(20).std()

    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (std * 2)

    # Ensure 'Adj Close' exists
    if 'Adj Close' not in df.columns:
        df['Adj Close'] = df['Close']

    return df.dropna()


def predict_price_lstm(symbol: str, days: int = 7, period: str = '1y') -> Dict[str, Any]:
    """Load yfinance history, load `model/lstm_model.pkl`, and return recursive predictions.

    Returns a JSON-serializable dict with keys: symbol, model, predictions, last_date, last_close.
    Raises FileNotFoundError, ModuleNotFoundError, ValueError, or other Exceptions on failure.
    """
    if not symbol:
        raise ValueError('No symbol provided')

    features = [
        'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume',
        'Daily_Return', 'Log_Return', 'MA10', 'MA20', 'MA50',
        'EMA10', 'EMA20', 'Volatility', 'RSI',
        'MACD', 'Signal_Line', 'BB_Middle', 'BB_Upper', 'BB_Lower'
    ]
    time_step = 60

    # Fetch initial data
    df = _get_features_df(symbol, period='1y')
    if len(df) < time_step:
        raise ValueError(f'Not enough historical data to create a feature window of {time_step} days.')

    last_date = pd.to_datetime(df.index[-1])
    last_close = float(df['Close'].iloc[-1])

    # Load models and scalers
    model_path = os.path.join('model', 'lstm_model.pkl')
    scaler_x_path = os.path.join('model', 'scaler_X.pkl')
    scaler_y_path = os.path.join('model', 'scaler_y.pkl')

    if not all(os.path.exists(p) for p in [model_path, scaler_x_path, scaler_y_path]):
        raise FileNotFoundError('A required model or scaler file is missing.')

    model = joblib.load(model_path)
    scaler_X = joblib.load(scaler_x_path)
    scaler_y = joblib.load(scaler_y_path)

    # Recursive prediction loop
    predictions_list = []
    current_df = df.copy()

    for i in range(1, days + 1):
        # Prepare input features from the last `time_step` days
        last_sequence_df = current_df[features].iloc[-time_step:]
        
        # Scale the 2D data (60, 20)
        scaled_sequence = scaler_X.transform(last_sequence_df)
        
        # Reshape for LSTM model
        X = scaled_sequence.reshape(1, time_step, len(features))

        # Predict one step ahead
        raw_pred = model.predict(X)
        
        # Inverse transform the prediction to get the actual price
        predicted_price = scaler_y.inverse_transform(raw_pred.reshape(-1, 1))[0][0]

        # Store the prediction
        next_pred_date = last_date + pd.Timedelta(days=i)
        predictions_list.append({'x': next_pred_date.strftime('%Y-%m-%d'), 'y': round(float(predicted_price), 4)})

        # Append the prediction to the dataframe to be used in the next iteration
        new_row = last_sequence_df.iloc[-1:].copy()
        new_row.index = [next_pred_date]
        # Use predicted price for all price-based columns
        for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
            new_row[col] = predicted_price
        
        # Append the new row and re-calculate features for the next step
        current_df = pd.concat([current_df, new_row])
        # A simple forward-fill for indicators. A full recalculation is too complex here.
        current_df.ffill(inplace=True)

    return {
        'symbol': symbol,
        'model': 'lstm_model.pkl',
        'predictions': predictions_list,
        'last_date': last_date.strftime('%Y-%m-%d'),
        'last_close': last_close
    }
