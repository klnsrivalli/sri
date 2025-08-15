import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import pandas as pd
import logging

from models import (
    Competitor, Product, PriceHistory, PriceAlert, ScrapingLog,
    SessionLocal, init_db
)
from scraper import scraping_manager, ScrapedProduct
from config import config, CompetitorConfig
from notifications import NotificationManager

logger = logging.getLogger(__name__)

class PriceMonitor:
    """Core price monitoring and comparison engine"""
    
    def __init__(self):
        self.notification_manager = NotificationManager()
        init_db()  # Ensure database is initialized
    
    def add_competitor(self, name: str, base_url: str, selectors: Dict[str, str]) -> int:
        """Add a new competitor to monitor"""
        db = SessionLocal()
        try:
            # Check if competitor already exists
            existing = db.query(Competitor).filter(Competitor.name == name).first()
            if existing:
                logger.info(f"Competitor {name} already exists")
                return existing.id
            
            competitor = Competitor(
                name=name,
                base_url=base_url
            )
            db.add(competitor)
            db.commit()
            db.refresh(competitor)
            
            # Add to config
            competitor_config = CompetitorConfig(
                name=name,
                base_url=base_url,
                product_urls=[],
                selectors=selectors
            )
            config.add_competitor(competitor_config)
            
            logger.info(f"Added competitor: {name}")
            return competitor.id
            
        finally:
            db.close()
    
    def add_product(self, competitor_name: str, product_name: str, url: str, 
                   sku: str = None, category: str = None) -> int:
        """Add a product to monitor for a competitor"""
        db = SessionLocal()
        try:
            # Get competitor
            competitor = db.query(Competitor).filter(
                Competitor.name == competitor_name
            ).first()
            
            if not competitor:
                raise ValueError(f"Competitor {competitor_name} not found")
            
            # Check if product already exists
            existing = db.query(Product).filter(
                Product.competitor_id == competitor.id,
                Product.url == url
            ).first()
            
            if existing:
                logger.info(f"Product {url} already exists for {competitor_name}")
                return existing.id
            
            product = Product(
                competitor_id=competitor.id,
                name=product_name,
                url=url,
                sku=sku,
                category=category
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            
            logger.info(f"Added product: {product_name} for {competitor_name}")
            return product.id
            
        finally:
            db.close()
    
    def scrape_and_store(self, product_id: int, use_selenium: bool = False) -> Optional[PriceHistory]:
        """Scrape a single product and store the results"""
        db = SessionLocal()
        try:
            # Get product and competitor info
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.error(f"Product {product_id} not found")
                return None
            
            competitor_config = config.get_competitor(product.competitor.name)
            if not competitor_config:
                logger.error(f"Competitor config for {product.competitor.name} not found")
                return None
            
            start_time = time.time()
            
            # Scrape the product
            scraped_data = scraping_manager.get_scraper(
                competitor_config, use_selenium
            ).scrape_product(product.url)
            
            response_time = time.time() - start_time
            
            # Log the scraping attempt
            log_entry = ScrapingLog(
                product_id=product_id,
                status="success" if scraped_data.price is not None else "failed",
                error_message=scraped_data.raw_data.get('error') if scraped_data.raw_data else None,
                response_time=response_time
            )
            db.add(log_entry)
            
            # Store price history if we got valid data
            if scraped_data.price is not None:
                price_entry = PriceHistory(
                    product_id=product_id,
                    price=scraped_data.price,
                    currency=scraped_data.currency,
                    availability=scraped_data.availability,
                    rating=scraped_data.rating,
                    reviews_count=scraped_data.reviews_count,
                    raw_data=json.dumps(scraped_data.raw_data) if scraped_data.raw_data else None
                )
                db.add(price_entry)
                db.commit()
                db.refresh(price_entry)
                
                logger.info(f"Stored price data for product {product.name}: ${scraped_data.price}")
                return price_entry
            else:
                db.commit()
                logger.warning(f"No price data found for product {product.name}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping product {product_id}: {str(e)}")
            # Log the error
            log_entry = ScrapingLog(
                product_id=product_id,
                status="failed",
                error_message=str(e),
                response_time=0
            )
            db.add(log_entry)
            db.commit()
            return None
        finally:
            db.close()
    
    def monitor_all_products(self, use_selenium: bool = False) -> Dict[str, any]:
        """Monitor all active products"""
        db = SessionLocal()
        results = {
            'total_products': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'price_changes': 0,
            'alerts_triggered': 0
        }
        
        try:
            # Get all active products
            products = db.query(Product).filter(Product.is_active == True).all()
            results['total_products'] = len(products)
            
            for product in products:
                try:
                    logger.info(f"Monitoring product: {product.name}")
                    
                    # Get previous price for comparison
                    previous_price = self.get_latest_price(product.id, db)
                    
                    # Scrape current data
                    price_entry = self.scrape_and_store(product.id, use_selenium)
                    
                    if price_entry:
                        results['successful_scrapes'] += 1
                        
                        # Check for price changes and trigger alerts
                        if previous_price and previous_price != price_entry.price:
                            results['price_changes'] += 1
                            
                            # Check price alerts
                            alerts = self.check_price_alerts(product.id, previous_price, price_entry.price, db)
                            results['alerts_triggered'] += len(alerts)
                    else:
                        results['failed_scrapes'] += 1
                    
                    # Add delay between products
                    competitor_config = config.get_competitor(product.competitor.name)
                    if competitor_config and competitor_config.delay > 0:
                        time.sleep(competitor_config.delay)
                        
                except Exception as e:
                    logger.error(f"Error monitoring product {product.id}: {str(e)}")
                    results['failed_scrapes'] += 1
            
            logger.info(f"Monitoring completed: {results}")
            return results
            
        finally:
            db.close()
    
    def get_latest_price(self, product_id: int, db: Session) -> Optional[float]:
        """Get the latest price for a product"""
        latest_entry = db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id
        ).order_by(desc(PriceHistory.scraped_at)).first()
        
        return latest_entry.price if latest_entry else None
    
    def check_price_alerts(self, product_id: int, old_price: float, 
                          new_price: float, db: Session) -> List[PriceAlert]:
        """Check if any price alerts should be triggered"""
        triggered_alerts = []
        
        # Get active alerts for this product
        alerts = db.query(PriceAlert).filter(
            PriceAlert.product_id == product_id,
            PriceAlert.is_active == True
        ).all()
        
        for alert in alerts:
            should_trigger = False
            change_percentage = ((new_price - old_price) / old_price) * 100
            
            if alert.alert_type == 'price_drop':
                if alert.threshold_percentage and change_percentage <= -alert.threshold_percentage:
                    should_trigger = True
                elif alert.threshold_value and new_price <= alert.threshold_value:
                    should_trigger = True
            
            elif alert.alert_type == 'price_increase':
                if alert.threshold_percentage and change_percentage >= alert.threshold_percentage:
                    should_trigger = True
                elif alert.threshold_value and new_price >= alert.threshold_value:
                    should_trigger = True
            
            if should_trigger:
                # Update alert last triggered time
                alert.last_triggered = datetime.utcnow()
                db.commit()
                
                # Send notification
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    self.notification_manager.send_price_alert(
                        product, old_price, new_price, alert.alert_type
                    )
                
                triggered_alerts.append(alert)
                logger.info(f"Triggered {alert.alert_type} alert for product {product_id}")
        
        return triggered_alerts
    
    def add_price_alert(self, product_id: int, alert_type: str, 
                       threshold_value: float = None, 
                       threshold_percentage: float = None) -> int:
        """Add a price alert for a product"""
        db = SessionLocal()
        try:
            alert = PriceAlert(
                product_id=product_id,
                alert_type=alert_type,
                threshold_value=threshold_value,
                threshold_percentage=threshold_percentage
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            logger.info(f"Added {alert_type} alert for product {product_id}")
            return alert.id
            
        finally:
            db.close()
    
    def get_price_history(self, product_id: int, days: int = 30) -> pd.DataFrame:
        """Get price history for a product as a pandas DataFrame"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            history = db.query(PriceHistory).filter(
                PriceHistory.product_id == product_id,
                PriceHistory.scraped_at >= cutoff_date
            ).order_by(PriceHistory.scraped_at).all()
            
            if not history:
                return pd.DataFrame()
            
            data = []
            for entry in history:
                data.append({
                    'date': entry.scraped_at,
                    'price': entry.price,
                    'currency': entry.currency,
                    'availability': entry.availability,
                    'rating': entry.rating,
                    'reviews_count': entry.reviews_count
                })
            
            return pd.DataFrame(data)
            
        finally:
            db.close()
    
    def compare_competitors(self, product_name_pattern: str) -> pd.DataFrame:
        """Compare prices across competitors for similar products"""
        db = SessionLocal()
        try:
            # Find products matching the pattern
            products = db.query(Product).filter(
                Product.name.contains(product_name_pattern),
                Product.is_active == True
            ).all()
            
            comparison_data = []
            
            for product in products:
                # Get latest price
                latest_price = db.query(PriceHistory).filter(
                    PriceHistory.product_id == product.id
                ).order_by(desc(PriceHistory.scraped_at)).first()
                
                if latest_price:
                    comparison_data.append({
                        'competitor': product.competitor.name,
                        'product_name': product.name,
                        'price': latest_price.price,
                        'currency': latest_price.currency,
                        'availability': latest_price.availability,
                        'rating': latest_price.rating,
                        'last_updated': latest_price.scraped_at,
                        'url': product.url
                    })
            
            return pd.DataFrame(comparison_data)
            
        finally:
            db.close()
    
    def get_monitoring_stats(self) -> Dict[str, any]:
        """Get overall monitoring statistics"""
        db = SessionLocal()
        try:
            stats = {}
            
            # Basic counts
            stats['total_competitors'] = db.query(Competitor).filter(Competitor.is_active == True).count()
            stats['total_products'] = db.query(Product).filter(Product.is_active == True).count()
            stats['total_price_entries'] = db.query(PriceHistory).count()
            stats['active_alerts'] = db.query(PriceAlert).filter(PriceAlert.is_active == True).count()
            
            # Recent activity (last 24 hours)
            cutoff = datetime.utcnow() - timedelta(days=1)
            stats['recent_scrapes'] = db.query(ScrapingLog).filter(
                ScrapingLog.scraped_at >= cutoff
            ).count()
            stats['recent_successes'] = db.query(ScrapingLog).filter(
                ScrapingLog.scraped_at >= cutoff,
                ScrapingLog.status == 'success'
            ).count()
            
            # Success rate
            if stats['recent_scrapes'] > 0:
                stats['success_rate'] = (stats['recent_successes'] / stats['recent_scrapes']) * 100
            else:
                stats['success_rate'] = 0
            
            return stats
            
        finally:
            db.close()

# Global monitor instance
price_monitor = PriceMonitor()