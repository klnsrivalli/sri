import os
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class CompetitorConfig:
    name: str
    base_url: str
    product_urls: List[str]
    selectors: Dict[str, str]  # CSS selectors for price, title, availability etc.
    headers: Dict[str, str] = None
    delay: int = 5  # Delay between requests in seconds

@dataclass
class NotificationConfig:
    email_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_user: str = ""
    email_password: str = ""
    recipients: List[str] = None

@dataclass
class MonitoringConfig:
    check_interval: int = 3600  # Check every hour by default
    price_change_threshold: float = 0.05  # 5% price change threshold
    store_history: bool = True
    max_retries: int = 3
    timeout: int = 30

class Config:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///competitor_monitoring.db")
        self.monitoring = MonitoringConfig()
        self.notifications = NotificationConfig(
            email_enabled=os.getenv("EMAIL_ENABLED", "false").lower() == "true",
            email_user=os.getenv("EMAIL_USER", ""),
            email_password=os.getenv("EMAIL_PASSWORD", ""),
            recipients=os.getenv("EMAIL_RECIPIENTS", "").split(",") if os.getenv("EMAIL_RECIPIENTS") else []
        )
        
        # Default competitor configurations
        self.competitors = [
            CompetitorConfig(
                name="Amazon",
                base_url="https://www.amazon.com",
                product_urls=[],
                selectors={
                    "price": ".a-price-whole, .a-price .a-offscreen",
                    "title": "#productTitle",
                    "availability": "#availability span",
                    "rating": ".a-icon-alt"
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            ),
            CompetitorConfig(
                name="eBay",
                base_url="https://www.ebay.com",
                product_urls=[],
                selectors={
                    "price": ".notranslate",
                    "title": ".x-item-title-label",
                    "availability": ".u-flL",
                    "rating": ".ebay-review-star-rating"
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            )
        ]
    
    def add_competitor(self, competitor: CompetitorConfig):
        """Add a new competitor configuration"""
        self.competitors.append(competitor)
    
    def get_competitor(self, name: str) -> CompetitorConfig:
        """Get competitor configuration by name"""
        for competitor in self.competitors:
            if competitor.name.lower() == name.lower():
                return competitor
        return None

# Global configuration instance
config = Config()