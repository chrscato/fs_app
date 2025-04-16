import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost/compensation_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET = os.getenv('S3_BUCKET')
    
    # Cache configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here') 