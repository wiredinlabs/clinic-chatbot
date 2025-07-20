import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        # OpenAI API Key
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        
        # Supabase Configuration
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        self.supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
        self.supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
        
        # Google Calendar credentials file
        self.google_calendar_credentials_file: str = os.getenv(
            "GOOGLE_CALENDAR_CREDENTIALS_FILE", 
            "credentials/google-credentials.json"
        )
        
        # Timezone & hours
        self.default_timezone: str = os.getenv("DEFAULT_TIMEZONE", "Asia/Karachi")
        self.default_start_hour: int = int(os.getenv("DEFAULT_START_HOUR", "9"))
        self.default_end_hour: int = int(os.getenv("DEFAULT_END_HOUR", "19"))
        self.default_appointment_duration: int = int(os.getenv("DEFAULT_APPOINTMENT_DURATION", "30"))
        
        # API settings
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.debug: bool = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        
        # Session and rate limiting
        # self.session_timeout_hours: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
        self.rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))

    def validate(self) -> bool:
        required = [
            ("OPENAI_API_KEY", self.openai_api_key),
            ("SUPABASE_URL", self.supabase_url),
            ("SUPABASE_ANON_KEY", self.supabase_anon_key),
        ]
        missing = [name for name, value in required if not value]
        if missing:
            print(f"❌ Missing required environment variables: {', '.join(missing)}")
            return False
        return True

# Create global instance
settings = Settings()
