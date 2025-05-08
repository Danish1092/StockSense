import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'stocksence.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Alpha Vantage API Key
    ALPHA_VANTAGE_API_KEY = 'your-api-key-here'
    
    # Other configurations
    ITEMS_PER_PAGE = 20
