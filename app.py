from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_session import Session
from auth import login_required, handle_login
from datetime import datetime
import os
import logging
import time
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Provide a fallback SECRET_KEY if not set in the environment
if not SECRET_KEY:
    SECRET_KEY = 'fallback-secret-key'  # Replace with a strong, random key
app.config['SECRET_KEY'] = SECRET_KEY

# Popup session tracking
@app.before_request
def show_popup_once():
    if 'popup_seen' not in session:
        session['popup_seen'] = False

# Set the default prediction model. 0 for XGBoost, 1 for LSTM.
app.config['DEFAULT_MODEL'] = 0

# Configure session management
app.config['SESSION_TYPE'] = 'filesystem'  # Store session data in the file system
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True  # Protect against session tampering
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session lifetime in seconds (1 hour)
Session(app)

# Import market data functions
from market_data import get_market_movers_cached, format_number_wrapper

# Basic routes
if __name__ == '__main__':
    # Run notifications first (blocking) then start a scheduler thread to run every 24 hours
    try:
        import notifications
        logging.info('Running notifications before server start')
        notifications.run_notifications()

        # Start background scheduler to re-run notifications every 24 hours
        import threading

        def _notifications_scheduler():
            while True:
                time.sleep(24 * 3600)
                try:
                    logging.info('Scheduled notifications run')
                    notifications.run_notifications()
                except Exception as e:
                    logging.exception('Scheduled notifications failed: %s', e)

        t = threading.Thread(target=_notifications_scheduler, daemon=True)
        t.start()
    except Exception as e:
        logging.exception('Failed to run/start notifications: %s', e)

    from routes import app
    app.run(debug=True, port=5000)
