import requests
import time
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base scraper class providing common functionality for all platform scrapers."""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.driver = None
        self.setup_session()
        
    def setup_session(self):
        """Setup the requests session with headers and proxies."""
        # Rotate user agents if enabled
        if settings.USER_AGENT_ROTATION:
            self.session.headers.update({
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
        
        # Setup proxy if enabled
        if settings.PROXY_ENABLED and settings.PROXY_URL:
            self.session.proxies = {
                'http': settings.PROXY_URL,
                'https': settings.PROXY_URL
            }
    
    def get_selenium_driver(self):
        """Get a configured Selenium WebDriver instance."""
        if self.driver is None:
            chrome_options = Options()
            
            if settings.HEADLESS_BROWSER:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={self.ua.random}")
            
            # Add additional options for better performance
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            
            try:
                self.driver = webdriver.Chrome(
                    service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
            except Exception as e:
                logger.error(f"Failed to initialize Chrome driver: {e}")
                raise
        
        return self.driver
    
    def close_driver(self):
        """Close the Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
            finally:
                self.driver = None
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make an HTTP request with retry logic and delays."""
        for attempt in range(settings.MAX_RETRIES):
            try:
                # Add random delay between requests
                time.sleep(settings.REQUEST_DELAY + random.uniform(0, 1))
                
                # Rotate user agent for each request
                if settings.USER_AGENT_ROTATION:
                    self.session.headers['User-Agent'] = self.ua.random
                
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                if attempt == settings.MAX_RETRIES - 1:
                    logger.error(f"All request attempts failed for {url}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def get_page_with_selenium(self, url: str, wait_for_element: Optional[str] = None) -> Optional[str]:
        """Get page content using Selenium with optional element waiting."""
        driver = self.get_selenium_driver()
        
        try:
            driver.get(url)
            
            # Wait for specific element if provided
            if wait_for_element:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                except TimeoutException:
                    logger.warning(f"Timeout waiting for element {wait_for_element} on {url}")
            
            # Add random delay to simulate human behavior
            time.sleep(random.uniform(1, 3))
            
            return driver.page_source
            
        except WebDriverException as e:
            logger.error(f"Selenium error for {url}: {e}")
            return None
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup."""
        return BeautifulSoup(html_content, 'html.parser')
    
    def extract_price(self, text: str) -> Optional[float]:
        """Extract price from text, handling various formats."""
        import re
        
        if not text:
            return None
        
        # Remove common currency symbols and extract numbers
        price_pattern = r'[\$£€¥]?[\d,]+\.?\d*'
        matches = re.findall(price_pattern, text)
        
        if matches:
            # Take the first match and clean it
            price_str = matches[0].replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                pass
        
        return None
    
    def extract_rating(self, text: str) -> Optional[float]:
        """Extract rating from text (e.g., '4.5 out of 5')."""
        import re
        
        if not text:
            return None
        
        # Look for patterns like "4.5 out of 5" or "4.5/5"
        rating_pattern = r'(\d+\.?\d*)\s*(?:out\s+of\s+|\/)\s*(\d+)'
        match = re.search(rating_pattern, text)
        
        if match:
            try:
                rating = float(match.group(1))
                max_rating = float(match.group(2))
                return (rating / max_rating) * 5  # Normalize to 5-star scale
            except ValueError:
                pass
        
        # Look for simple decimal ratings
        simple_pattern = r'(\d+\.?\d*)'
        match = re.search(simple_pattern, text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        return None
    
    def extract_review_count(self, text: str) -> Optional[int]:
        """Extract review count from text."""
        import re
        
        if not text:
            return None
        
        # Look for patterns like "1,234 reviews" or "1234 reviews"
        pattern = r'([\d,]+)\s*reviews?'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                return int(match.group(1).replace(',', ''))
            except ValueError:
                pass
        
        return None
    
    def is_in_stock(self, text: str) -> bool:
        """Determine if product is in stock based on text."""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Stock indicators
        in_stock_indicators = [
            'in stock', 'available', 'add to cart', 'buy now',
            'add to basket', 'purchase', 'order now'
        ]
        
        out_of_stock_indicators = [
            'out of stock', 'unavailable', 'sold out', 'backorder',
            'pre-order', 'coming soon', 'temporarily unavailable'
        ]
        
        # Check for out of stock indicators first
        for indicator in out_of_stock_indicators:
            if indicator in text_lower:
                return False
        
        # Check for in stock indicators
        for indicator in in_stock_indicators:
            if indicator in text_lower:
                return True
        
        # Default to available if no clear indicators
        return True
    
    @abstractmethod
    def scrape_product(self, url: str) -> Dict[str, Any]:
        """Scrape product information from a URL. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name. Must be implemented by subclasses."""
        pass
    
    def __del__(self):
        """Cleanup when the scraper is destroyed."""
        self.close_driver()