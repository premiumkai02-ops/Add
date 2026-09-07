import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Userbot Configuration
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')
    PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
    SESSION_NAME = os.getenv('SESSION_NAME', 'userbot_session')
    
    # Target Group
    TARGET_GROUP = os.getenv('TARGET_GROUP', '')
    
    # Website Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    PORT = int(os.getenv('PORT', 8080))
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Database (SQLite - មិនត្រូវការ Service ដាច់ដោយឡែក)
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'telegram_bot.db')
    
    @classmethod
    def validate(cls):
        required = ['API_ID', 'API_HASH', 'PHONE_NUMBER', 'TARGET_GROUP']
        for field in required:
            if not getattr(cls, field, None):
                raise ValueError(f"{field} មិនត្រូវបានកំណត់!")
        return True
