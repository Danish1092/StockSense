from flask import redirect, url_for, flash, session
from supabase import create_client
from email_service import EmailService
from functools import wraps
import random
import string
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
import bcrypt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()


# Use supabase client from config.py
from config import supabase

email_service = EmailService()

# Simple file-based storage for users
USERS_FILE = 'users.json'

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def generate_verification_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def handle_signup_request(email, password, username):
    """
    Step 1: Called when user submits signup form. Generates OTP, sends email, stores data in session.
    """
    try:
        # Check if user already exists
        result = supabase.table('users').select('id').eq('email', email).execute()
        if result.data:
            return False, "Email already registered."

        otp = generate_verification_code()
        # Store signup data and OTP in session
        session['pending_signup'] = {
            'email': email,
            'password': password,
            'username': username,
            'otp': otp,
            'otp_expires': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        # Send OTP email
        email_service.send_verification_email(email, otp)
        return True, "Verification code sent to your email."
    except Exception as e:
        logging.error(f"Signup request error: {e}")
        return False, "Failed to send verification code."

def handle_signup_otp(otp_input):
    """
    Step 2: Called when user submits OTP. Verifies OTP and creates user if valid.
    """
    try:
        pending = session.get('pending_signup')
        if not pending:
            return False, "No signup in progress. Please start again."
        if datetime.utcnow() > datetime.fromisoformat(pending['otp_expires']):
            session.pop('pending_signup', None)
            return False, "Verification code expired. Please sign up again."
        if otp_input != pending['otp']:
            return False, "Invalid verification code."

        # Hash the password
        hashed_password = bcrypt.hashpw(pending['password'].encode('utf-8'), bcrypt.gensalt())
        data = {
            'email': pending['email'],
            'password_hash': hashed_password.decode('utf-8'),
            'full_name': pending['username'],
            'created_at': str(datetime.utcnow()),
            'updated_at': str(datetime.utcnow())
        }
        supabase.table('users').insert(data).execute()
        session.pop('pending_signup', None)
        return True, "Account created successfully."
    except Exception as e:
        logging.error(f"Signup OTP error: {e}")
        return False, "Failed to create account."

def handle_login(email, password):
    try:
        # Query user from Supabase
        result = supabase.table('users').select('*').eq('email', email).execute()
        if result.data:
            user = result.data[0]
            # Verify the password using 'password_hash' field
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return True
        return False
    except Exception as e:
        logging.error(f"Login error: {e}")
        return False

def handle_password_reset(email):
    try:
        reset_code = generate_verification_code()
        
        # Update reset code in Supabase
        supabase.table('users').update({
            'reset_code': reset_code,
            'reset_code_expires': str(datetime.utcnow() + timedelta(minutes=10))
        }).eq('email', email).execute()
        
        # Send reset email
        if email_service.send_password_reset_email(email, reset_code):
            return True, "Password reset instructions sent to your email"
        return False, "Failed to send reset email"
        
    except Exception as e:
        return False, str(e)
