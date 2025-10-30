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

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

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

def handle_signup(email, password, username):
    try:
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Store user data in Supabase
        data = {
            'email': email,
            'username': username,
            'password': hashed_password.decode('utf-8'),  # Store hashed password
            'created_at': str(datetime.utcnow())
        }
        
        result = supabase.table('users').insert(data).execute()
        return True
    except Exception as e:
        logging.error(f"Signup error: {e}")
        return False

def handle_login(email, password):
    try:
        # Query user from Supabase
        result = supabase.table('users').select('*').eq('email', email).execute()
        
        if result.data:
            user = result.data[0]
            # Verify the password
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
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
