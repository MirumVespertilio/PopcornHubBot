import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    @classmethod
    def validate(cls):
        missing = []
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        if not cls.TMDB_API_KEY:
            print("⚠️  TMDB_API_KEY not found - movie search will be disabled")
        if not cls.GEMINI_API_KEY:
            print("⚠️  GEMINI_API_KEY not found - AI features will be disabled")
        
        if missing:
            raise Exception(f"Missing required environment variables: {', '.join(missing)}")

config = Config()
