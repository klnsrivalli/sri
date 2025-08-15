import requests
import time
import random
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import logging
from config import settings, COMPETITOR_CONFIGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.setup_session()
        
    def setup_session(self):
        """Setup session with headers and proxies"""
        self.session.headers.update({
            'User-Agent': self.ua.random if settings.ROTATE_USER_AGENTS else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        if settings.USE_PROXY and settings.PROXY_LIST:
            proxy = random.choice(settings.PROXY_LIST)
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
    
    def get_selenium_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Get configured Selenium WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={self.ua.random}")
        
        # Add additional options to avoid detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def scrape_with_requests(self, url: str, retries: int = None) -> Optional[BeautifulSoup]:
        """Scrape webpage using requests and BeautifulSoup"""
        if retries is None:
            retries = settings.MAX_RETRIES
            
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=settings.REQUEST_TIMEOUT)
                response.raise_for_status()
                
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(2, 5))
                else:
                    logger.error(f"Failed to scrape {url} after {retries} attempts")
                    return None
    
    def scrape_with_selenium(self, url: str, wait_for_element: str = None, timeout: int = 10) -> Optional[BeautifulSoup]:
        """Scrape webpage using Selenium (for JavaScript-heavy sites)"""
        driver = None
        try:
            driver = self.get_selenium_driver()
            driver.get(url)
            
            if wait_for_element:
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )
            
            # Add random delay
            time.sleep(random.uniform(2, 4))
            
            page_source = driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except TimeoutException:
            logger.warning(f"Timeout waiting for element {wait_for_element} on {url}")
            if driver:
                return BeautifulSoup(driver.page_source, 'html.parser')
        except Exception as e:
            logger.error(f"Error scraping {url} with Selenium: {e}")
        finally:
            if driver:
                driver.quit()
        
        return None
    
    def extract_price(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[float]:
        """Extract price from HTML using multiple selectors"""
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    # Remove currency symbols and convert to float
                    price_text = ''.join(c for c in text if c.isdigit() or c == '.')
                    if price_text:
                        return float(price_text)
            except Exception as e:
                logger.debug(f"Failed to extract price with selector {selector}: {e}")
                continue
        return None
    
    def extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text from HTML using multiple selectors"""
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text:
                        return text
            except Exception as e:
                logger.debug(f"Failed to extract text with selector {selector}: {e}")
                continue
        return None
    
    def check_availability(self, soup: BeautifulSoup, selectors: List[str]) -> Tuple[bool, str]:
        """Check product availability"""
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip().lower()
                    if any(keyword in text for keyword in ['in stock', 'available', 'add to cart']):
                        return True, 'in_stock'
                    elif any(keyword in text for keyword in ['out of stock', 'unavailable', 'sold out']):
                        return False, 'out_of_stock'
                    elif any(keyword in text for keyword in ['limited', 'few left']):
                        return True, 'limited'
            except Exception as e:
                logger.debug(f"Failed to check availability with selector {selector}: {e}")
                continue
        
        return False, 'unknown'

class CompetitorScraper(WebScraper):
    def __init__(self, competitor_name: str):
        super().__init__()
        self.competitor_name = competitor_name
        self.config = COMPETITOR_CONFIGS.get(competitor_name.lower())
        
        if not self.config:
            raise ValueError(f"No configuration found for competitor: {competitor_name}")
    
    def search_products(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for products on competitor site"""
        results = []
        
        try:
            # Construct search URL
            search_url = f"{self.config['search_url']}?q={query}"
            
            # Use Selenium for JavaScript-heavy sites
            soup = self.scrape_with_selenium(search_url)
            
            if not soup:
                return results
            
            # Extract product information
            # This is a generic approach - specific implementation would depend on the site structure
            product_elements = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['product', 'item', 'card']
            ))
            
            for element in product_elements[:max_results]:
                product_data = self.extract_product_data(element)
                if product_data:
                    results.append(product_data)
            
        except Exception as e:
            logger.error(f"Error searching products on {self.competitor_name}: {e}")
        
        return results
    
    def extract_product_data(self, element) -> Optional[Dict]:
        """Extract product data from HTML element"""
        try:
            # Extract title
            title = self.extract_text(element, self.config['title_selectors'])
            
            # Extract price
            price = self.extract_price(element, self.config['price_selectors'])
            
            # Extract availability
            is_available, availability_status = self.check_availability(element, self.config['availability_selectors'])
            
            # Extract URL
            url_element = element.find('a', href=True)
            url = url_element['href'] if url_element else None
            if url and not url.startswith('http'):
                url = self.config['base_url'] + url
            
            if title and price:
                return {
                    'title': title,
                    'price': price,
                    'is_available': is_available,
                    'availability_status': availability_status,
                    'url': url,
                    'competitor': self.competitor_name
                }
        
        except Exception as e:
            logger.debug(f"Error extracting product data: {e}")
        
        return None
    
    def get_product_details(self, url: str) -> Optional[Dict]:
        """Get detailed product information from product page"""
        try:
            soup = self.scrape_with_selenium(url)
            
            if not soup:
                return None
            
            # Extract detailed information
            title = self.extract_text(soup, self.config['title_selectors'])
            price = self.extract_price(soup, self.config['price_selectors'])
            is_available, availability_status = self.check_availability(soup, self.config['availability_selectors'])
            
            # Extract additional information
            description = self.extract_text(soup, ['p', 'div'], lambda x: x and 'description' in x.lower())
            brand = self.extract_text(soup, ['span', 'div'], lambda x: x and 'brand' in x.lower())
            
            return {
                'title': title,
                'price': price,
                'is_available': is_available,
                'availability_status': availability_status,
                'description': description,
                'brand': brand,
                'url': url,
                'competitor': self.competitor_name
            }
        
        except Exception as e:
            logger.error(f"Error getting product details from {url}: {e}")
            return None