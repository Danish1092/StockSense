
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
