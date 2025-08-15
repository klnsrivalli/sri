import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///competitor_monitor.db")
    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Monitoring settings
    MONITORING_INTERVAL_MINUTES: int = int(os.getenv("MONITORING_INTERVAL_MINUTES", "60"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Proxy settings (optional)
    USE_PROXY: bool = os.getenv("USE_PROXY", "False").lower() == "true"
    PROXY_LIST: List[str] = os.getenv("PROXY_LIST", "").split(",") if os.getenv("PROXY_LIST") else []
    
    # Notification settings
    ENABLE_NOTIFICATIONS: bool = os.getenv("ENABLE_NOTIFICATIONS", "True").lower() == "true"
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    EMAIL_SMTP_SERVER: Optional[str] = os.getenv("EMAIL_SMTP_SERVER")
    EMAIL_USERNAME: Optional[str] = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD: Optional[str] = os.getenv("EMAIL_PASSWORD")
    
    # Price change thresholds
    PRICE_CHANGE_THRESHOLD_PERCENT: float = float(os.getenv("PRICE_CHANGE_THRESHOLD_PERCENT", "5.0"))
    
    # User agent rotation
    ROTATE_USER_AGENTS: bool = os.getenv("ROTATE_USER_AGENTS", "True").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Competitor configurations
COMPETITOR_CONFIGS = {
    "amazon": {
        "base_url": "https://www.amazon.com",
        "search_url": "https://www.amazon.com/s",
        "price_selectors": [
            "span.a-price-whole",
            "span.a-price-fraction",
            "span.a-offscreen"
        ],
        "title_selectors": [
            "span.a-size-medium.a-color-base.a-text-normal",
            "h2.a-size-mini.a-spacing-none.a-color-base"
        ],
        "availability_selectors": [
            "span.a-size-medium.a-color-success",
            "span.a-size-medium.a-color-price"
        ]
    },
    "walmart": {
        "base_url": "https://www.walmart.com",
        "search_url": "https://www.walmart.com/search",
        "price_selectors": [
            "span.price-characteristic",
            "span.price-main"
        ],
        "title_selectors": [
            "span.normal.dark-gray",
            "a.link-normal"
        ],
        "availability_selectors": [
            "span.prod-ProductOffer"
        ]
    },
    "target": {
        "base_url": "https://www.target.com",
        "search_url": "https://www.target.com/s",
        "price_selectors": [
            "span[data-test='current-price']",
            "span[data-test='price-current-price']"
        ],
        "title_selectors": [
            "a[data-test='product-title']",
            "h3[data-test='product-title']"
        ],
        "availability_selectors": [
            "span[data-test='shipItButton']",
            "span[data-test='orderPickupButton']"
        ]
    }
}