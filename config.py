import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Secret key for signing session cookies
SECRET_KEY = 'your-secret-key-here'  # Replace with a strong, random key

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
