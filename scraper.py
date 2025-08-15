import asyncio
import aiohttp
import requests
import time
import json
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass
import logging
from config import CompetitorConfig, config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScrapedProduct:
    url: str
    title: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"
    availability: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    raw_data: Dict[str, Any] = None
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.utcnow()

class BaseScraper:
    """Base scraper class with common functionality"""
    
    def __init__(self, competitor_config: CompetitorConfig):
        self.config = competitor_config
        self.ua = UserAgent()
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Setup requests session with headers and other configurations"""
        headers = self.config.headers or {}
        if "User-Agent" not in headers:
            headers["User-Agent"] = self.ua.random
        
        self.session.headers.update(headers)
        self.session.timeout = config.monitoring.timeout
    
    def extract_price(self, text: str) -> Optional[float]:
        """Extract price from text using regex"""
        if not text:
            return None
        
        # Remove common currency symbols and text
        text = re.sub(r'[^\d.,]', '', text.replace(',', ''))
        
        # Find price patterns
        price_patterns = [
            r'(\d+\.?\d*)',
            r'(\d+,\d+\.?\d*)',
            r'(\d+)',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def extract_rating(self, text: str) -> Optional[float]:
        """Extract rating from text"""
        if not text:
            return None
        
        # Look for rating patterns like "4.5 out of 5", "4.5/5", "4.5 stars"
        rating_patterns = [
            r'(\d+\.?\d*)\s*out\s*of\s*5',
            r'(\d+\.?\d*)/5',
            r'(\d+\.?\d*)\s*star',
            r'(\d+\.?\d*)',
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    rating = float(match.group(1))
                    if 0 <= rating <= 5:
                        return rating
                except ValueError:
                    continue
        
        return None

class RequestsScraper(BaseScraper):
    """Scraper using requests and BeautifulSoup"""
    
    def scrape_product(self, url: str) -> ScrapedProduct:
        """Scrape a single product using requests"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract data using configured selectors
            title = self.extract_text(soup, self.config.selectors.get('title'))
            price_text = self.extract_text(soup, self.config.selectors.get('price'))
            availability = self.extract_text(soup, self.config.selectors.get('availability'))
            rating_text = self.extract_text(soup, self.config.selectors.get('rating'))
            
            # Process extracted data
            price = self.extract_price(price_text) if price_text else None
            rating = self.extract_rating(rating_text) if rating_text else None
            
            # Try to extract image
            image_url = None
            img_selector = self.config.selectors.get('image')
            if img_selector:
                img_element = soup.select_one(img_selector)
                if img_element:
                    image_url = img_element.get('src') or img_element.get('data-src')
            
            return ScrapedProduct(
                url=url,
                title=title,
                price=price,
                availability=availability,
                rating=rating,
                image_url=image_url,
                raw_data={
                    'title_text': title,
                    'price_text': price_text,
                    'availability_text': availability,
                    'rating_text': rating_text,
                    'response_status': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return ScrapedProduct(
                url=url,
                raw_data={'error': str(e), 'scraper_type': 'requests'}
            )
    
    def extract_text(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Extract text from soup using CSS selector"""
        if not selector:
            return None
        
        try:
            elements = soup.select(selector)
            if elements:
                # Try multiple elements and return the first non-empty one
                for element in elements:
                    text = element.get_text(strip=True)
                    if text:
                        return text
        except Exception as e:
            logger.warning(f"Error extracting text with selector '{selector}': {str(e)}")
        
        return None

class SeleniumScraper(BaseScraper):
    """Scraper using Selenium for dynamic content"""
    
    def __init__(self, competitor_config: CompetitorConfig):
        super().__init__(competitor_config)
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.ua.random}')
        
        try:
            self.driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.driver.implicitly_wait(10)
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {str(e)}")
            self.driver = None
    
    def scrape_product(self, url: str) -> ScrapedProduct:
        """Scrape a single product using Selenium"""
        if not self.driver:
            return ScrapedProduct(
                url=url,
                raw_data={'error': 'Chrome driver not available', 'scraper_type': 'selenium'}
            )
        
        try:
            start_time = time.time()
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract data using configured selectors
            title = self.extract_text_selenium(self.config.selectors.get('title'))
            price_text = self.extract_text_selenium(self.config.selectors.get('price'))
            availability = self.extract_text_selenium(self.config.selectors.get('availability'))
            rating_text = self.extract_text_selenium(self.config.selectors.get('rating'))
            
            # Process extracted data
            price = self.extract_price(price_text) if price_text else None
            rating = self.extract_rating(rating_text) if rating_text else None
            
            # Try to extract image
            image_url = None
            img_selector = self.config.selectors.get('image')
            if img_selector:
                try:
                    img_element = self.driver.find_element(By.CSS_SELECTOR, img_selector)
                    image_url = img_element.get_attribute('src') or img_element.get_attribute('data-src')
                except:
                    pass
            
            response_time = time.time() - start_time
            
            return ScrapedProduct(
                url=url,
                title=title,
                price=price,
                availability=availability,
                rating=rating,
                image_url=image_url,
                raw_data={
                    'title_text': title,
                    'price_text': price_text,
                    'availability_text': availability,
                    'rating_text': rating_text,
                    'response_time': response_time,
                    'scraper_type': 'selenium'
                }
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url} with Selenium: {str(e)}")
            return ScrapedProduct(
                url=url,
                raw_data={'error': str(e), 'scraper_type': 'selenium'}
            )
    
    def extract_text_selenium(self, selector: str) -> Optional[str]:
        """Extract text using Selenium"""
        if not selector:
            return None
        
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                text = element.text.strip()
                if text:
                    return text
        except Exception as e:
            logger.warning(f"Error extracting text with selector '{selector}': {str(e)}")
        
        return None
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

class ScrapingManager:
    """Manages scraping operations for multiple competitors"""
    
    def __init__(self):
        self.scrapers = {}
        self.selenium_scrapers = {}
    
    def get_scraper(self, competitor_config: CompetitorConfig, use_selenium: bool = False) -> BaseScraper:
        """Get or create a scraper for the competitor"""
        key = competitor_config.name
        
        if use_selenium:
            if key not in self.selenium_scrapers:
                self.selenium_scrapers[key] = SeleniumScraper(competitor_config)
            return self.selenium_scrapers[key]
        else:
            if key not in self.scrapers:
                self.scrapers[key] = RequestsScraper(competitor_config)
            return self.scrapers[key]
    
    def scrape_products(self, competitor_config: CompetitorConfig, 
                       product_urls: List[str], use_selenium: bool = False) -> List[ScrapedProduct]:
        """Scrape multiple products"""
        scraper = self.get_scraper(competitor_config, use_selenium)
        results = []
        
        for url in product_urls:
            try:
                result = scraper.scrape_product(url)
                results.append(result)
                
                # Add delay between requests
                if competitor_config.delay > 0:
                    time.sleep(competitor_config.delay)
                    
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                results.append(ScrapedProduct(
                    url=url,
                    raw_data={'error': str(e)}
                ))
        
        return results
    
    def close_all(self):
        """Close all selenium scrapers"""
        for scraper in self.selenium_scrapers.values():
            if isinstance(scraper, SeleniumScraper):
                scraper.close()
        self.selenium_scrapers.clear()

# Global scraping manager instance
scraping_manager = ScrapingManager()