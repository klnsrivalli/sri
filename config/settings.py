import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./competitor_monitor.db")
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    
    # Email
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USER: Optional[str] = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD: Optional[str] = os.getenv("EMAIL_PASSWORD")
    
    # Monitoring
    MONITORING_INTERVAL: int = int(os.getenv("MONITORING_INTERVAL", "3600"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "2"))
    USER_AGENT_ROTATION: bool = os.getenv("USER_AGENT_ROTATION", "true").lower() == "true"
    
    # Scraping
    HEADLESS_BROWSER: bool = os.getenv("HEADLESS_BROWSER", "true").lower() == "true"
    PROXY_ENABLED: bool = os.getenv("PROXY_ENABLED", "false").lower() == "true"
    PROXY_URL: Optional[str] = os.getenv("PROXY_URL")
    
    # Alerts
    PRICE_CHANGE_THRESHOLD: float = float(os.getenv("PRICE_CHANGE_THRESHOLD", "0.05"))
    STOCK_ALERT_ENABLED: bool = os.getenv("STOCK_ALERT_ENABLED", "true").lower() == "true"
    PROMOTION_ALERT_ENABLED: bool = os.getenv("PROMOTION_ALERT_ENABLED", "true").lower() == "true"
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_DEBUG: bool = os.getenv("API_DEBUG", "false").lower() == "true"
    
    # Dashboard
    DASHBOARD_HOST: str = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "8050"))

# Global settings instance
settings = Settings()