from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class AmazonScraper(BaseScraper):
    """Amazon-specific scraper for extracting product information."""
    
    def __init__(self):
        super().__init__()
        self.selectors = {
            'title': [
                '#productTitle',
                'h1.a-size-large',
                '.a-size-large.a-spacing-none'
            ],
            'price': [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '#priceblock_ourprice',
                '#priceblock_dealprice',
                '.a-price-range .a-offscreen'
            ],
            'rating': [
                '.a-icon-alt',
                '.a-icon-star-small .a-icon-alt',
                '[data-hook="rating-out-of-text"]'
            ],
            'review_count': [
                '#acrCustomerReviewText',
                '[data-hook="total-review-count"]',
                '.a-size-base.a-color-secondary'
            ],
            'availability': [
                '#availability',
                '#availability span',
                '.a-size-medium.a-color-success'
            ],
            'shipping': [
                '#price-shipping-message',
                '.a-size-base.a-color-secondary.a-text-bold'
            ],
            'promotion': [
                '.a-box-inner .a-text-bold',
                '.a-color-price',
                '.a-size-base.a-color-price'
            ]
        }
    
    def get_platform_name(self) -> str:
        return "Amazon"
    
    def scrape_product(self, url: str) -> Dict[str, Any]:
        """Scrape product information from Amazon product page."""
        try:
            # Use Selenium for Amazon as it has dynamic content
            html_content = self.get_page_with_selenium(url, wait_for_element='#productTitle')
            
            if not html_content:
                logger.error(f"Failed to get content from {url}")
                return {}
            
            soup = self.parse_html(html_content)
            
            # Extract product information
            product_data = {
                'title': self._extract_title(soup),
                'price': self._extract_price(soup),
                'currency': 'USD',  # Default for Amazon US
                'rating': self._extract_rating(soup),
                'review_count': self._extract_review_count(soup),
                'is_available': self._extract_availability(soup),
                'stock_status': self._get_stock_status(soup),
                'shipping_cost': self._extract_shipping_cost(soup),
                'promotion_text': self._extract_promotion(soup),
                'url': url
            }
            
            logger.info(f"Successfully scraped Amazon product: {product_data.get('title', 'Unknown')}")
            return product_data
            
        except Exception as e:
            logger.error(f"Error scraping Amazon product {url}: {e}")
            return {}
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product title."""
        for selector in self.selectors['title']:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title:
                    return title
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product price."""
        for selector in self.selectors['price']:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                price = self.extract_price(price_text)
                if price:
                    return price
        
        # Try to find price in structured data
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    offers = data['offers']
                    if isinstance(offers, list) and offers:
                        price = offers[0].get('price')
                        if price:
                            return float(price)
                    elif isinstance(offers, dict):
                        price = offers.get('price')
                        if price:
                            return float(price)
            except (json.JSONDecodeError, (ValueError, TypeError)):
                continue
        
        return None
    
    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product rating."""
        for selector in self.selectors['rating']:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text(strip=True)
                rating = self.extract_rating(rating_text)
                if rating:
                    return rating
        
        # Try to find rating in structured data
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and 'aggregateRating' in data:
                    rating = data['aggregateRating'].get('ratingValue')
                    if rating:
                        return float(rating)
            except (json.JSONDecodeError, (ValueError, TypeError)):
                continue
        
        return None
    
    def _extract_review_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract review count."""
        for selector in self.selectors['review_count']:
            element = soup.select_one(selector)
            if element:
                review_text = element.get_text(strip=True)
                count = self.extract_review_count(review_text)
                if count:
                    return count
        
        # Try to find review count in structured data
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and 'aggregateRating' in data:
                    count = data['aggregateRating'].get('reviewCount')
                    if count:
                        return int(count)
            except (json.JSONDecodeError, (ValueError, TypeError)):
                continue
        
        return None
    
    def _extract_availability(self, soup: BeautifulSoup) -> bool:
        """Extract product availability."""
        for selector in self.selectors['availability']:
            element = soup.select_one(selector)
            if element:
                availability_text = element.get_text(strip=True)
                return self.is_in_stock(availability_text)
        
        # Default to available if no clear indicators
        return True
    
    def _get_stock_status(self, soup: BeautifulSoup) -> str:
        """Get detailed stock status."""
        for selector in self.selectors['availability']:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True).lower()
                
                if 'out of stock' in text or 'unavailable' in text:
                    return 'out_of_stock'
                elif 'limited' in text or 'only' in text:
                    return 'limited'
                elif 'in stock' in text or 'available' in text:
                    return 'in_stock'
                elif 'pre-order' in text:
                    return 'pre_order'
        
        return 'unknown'
    
    def _extract_shipping_cost(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract shipping cost."""
        for selector in self.selectors['shipping']:
            element = soup.select_one(selector)
            if element:
                shipping_text = element.get_text(strip=True)
                # Look for shipping cost patterns
                if 'free' in shipping_text.lower():
                    return 0.0
                
                # Extract numeric shipping cost
                import re
                cost_match = re.search(r'[\$£€¥]?(\d+\.?\d*)', shipping_text)
                if cost_match:
                    try:
                        return float(cost_match.group(1))
                    except ValueError:
                        continue
        
        return None
    
    def _extract_promotion(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract promotion information."""
        promotions = []
        
        for selector in self.selectors['promotion']:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 5:  # Filter out very short text
                    promotions.append(text)
        
        # Also look for deal badges
        deal_badges = soup.select('.a-badge-text')
        for badge in deal_badges:
            text = badge.get_text(strip=True)
            if text:
                promotions.append(text)
        
        if promotions:
            return '; '.join(promotions[:3])  # Limit to 3 promotions
        
        return None