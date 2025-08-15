from typing import Dict, Type
from .base_scraper import BaseScraper
from .amazon_scraper import AmazonScraper

# Registry of available scrapers
SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
    'amazon': AmazonScraper,
    'amazon.com': AmazonScraper,
    'www.amazon.com': AmazonScraper,
}

def get_scraper_for_url(url: str) -> BaseScraper:
    """Get the appropriate scraper for a given URL."""
    from urllib.parse import urlparse
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # Remove www. prefix for matching
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Try to find exact match
    if domain in SCRAPER_REGISTRY:
        return SCRAPER_REGISTRY[domain]()
    
    # Try partial matches
    for key, scraper_class in SCRAPER_REGISTRY.items():
        if key in domain:
            return scraper_class()
    
    # Default to base scraper if no match found
    from .base_scraper import BaseScraper
    return BaseScraper()

def register_scraper(domain: str, scraper_class: Type[BaseScraper]):
    """Register a new scraper for a domain."""
    SCRAPER_REGISTRY[domain.lower()] = scraper_class

def get_available_scrapers() -> Dict[str, Type[BaseScraper]]:
    """Get all available scrapers."""
    return SCRAPER_REGISTRY.copy()