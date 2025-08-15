import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import (
    get_db, Competitor, Product, PriceHistory, AvailabilityHistory, 
    MonitoringSession, Alert, init_db
)
from scraper import CompetitorScraper
from config import settings
from notifications import NotificationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompetitorMonitor:
    def __init__(self):
        self.notification_manager = NotificationManager()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.is_running = False
        
    def start_monitoring_session(self, session_name: str = None) -> MonitoringSession:
        """Start a new monitoring session"""
        if not session_name:
            session_name = f"monitoring_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        db = next(get_db())
        try:
            session = MonitoringSession(
                session_name=session_name,
                status="running"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info(f"Started monitoring session: {session_name}")
            return session
        finally:
            db.close()
    
    def end_monitoring_session(self, session_id: int, status: str = "completed", error_log: str = None):
        """End a monitoring session"""
        db = next(get_db())
        try:
            session = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
            if session:
                session.end_time = datetime.utcnow()
                session.status = status
                if error_log:
                    session.error_log = error_log
                db.commit()
                logger.info(f"Ended monitoring session {session_id} with status: {status}")
        finally:
            db.close()
    
    def monitor_competitor_products(self, competitor_name: str, products: List[Dict]) -> Dict:
        """Monitor products for a specific competitor"""
        results = {
            'competitor': competitor_name,
            'products_monitored': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'price_changes': 0,
            'availability_changes': 0,
            'errors': []
        }
        
        try:
            scraper = CompetitorScraper(competitor_name)
            
            for product_data in products:
                results['products_monitored'] += 1
                
                try:
                    # Get current product data
                    current_data = scraper.get_product_details(product_data['url'])
                    
                    if current_data:
                        results['successful_scrapes'] += 1
                        
                        # Check for price changes
                        if self._check_price_change(product_data, current_data):
                            results['price_changes'] += 1
                            self._create_price_alert(product_data, current_data)
                        
                        # Check for availability changes
                        if self._check_availability_change(product_data, current_data):
                            results['availability_changes'] += 1
                            self._create_availability_alert(product_data, current_data)
                        
                        # Update database
                        self._update_product_data(product_data, current_data)
                    
                    else:
                        results['failed_scrapes'] += 1
                        results['errors'].append(f"Failed to scrape {product_data['url']}")
                
                except Exception as e:
                    results['failed_scrapes'] += 1
                    results['errors'].append(f"Error monitoring product {product_data.get('title', 'Unknown')}: {str(e)}")
                    logger.error(f"Error monitoring product: {e}")
        
        except Exception as e:
            results['errors'].append(f"Error initializing scraper for {competitor_name}: {str(e)}")
            logger.error(f"Error initializing scraper for {competitor_name}: {e}")
        
        return results
    
    def _check_price_change(self, old_data: Dict, new_data: Dict) -> bool:
        """Check if price has changed significantly"""
        old_price = old_data.get('price')
        new_price = new_data.get('price')
        
        if old_price and new_price and old_price > 0:
            change_percent = abs(new_price - old_price) / old_price * 100
            return change_percent >= settings.PRICE_CHANGE_THRESHOLD_PERCENT
        
        return False
    
    def _check_availability_change(self, old_data: Dict, new_data: Dict) -> bool:
        """Check if availability has changed"""
        old_available = old_data.get('is_available')
        new_available = new_data.get('is_available')
        
        return old_available != new_available
    
    def _create_price_alert(self, old_data: Dict, new_data: Dict):
        """Create price change alert"""
        old_price = old_data.get('price', 0)
        new_price = new_data.get('price', 0)
        change_percent = ((new_price - old_price) / old_price * 100) if old_price > 0 else 0
        
        message = f"Price change detected for {new_data.get('title', 'Unknown Product')}: " \
                  f"${old_price:.2f} → ${new_price:.2f} ({change_percent:+.1f}%)"
        
        severity = "high" if abs(change_percent) > 10 else "medium" if abs(change_percent) > 5 else "low"
        
        self._create_alert(
            product_id=old_data.get('id'),
            alert_type="price_change",
            message=message,
            severity=severity,
            metadata={
                'old_price': old_price,
                'new_price': new_price,
                'change_percent': change_percent,
                'competitor': new_data.get('competitor')
            }
        )
    
    def _create_availability_alert(self, old_data: Dict, new_data: Dict):
        """Create availability change alert"""
        old_status = "Available" if old_data.get('is_available') else "Unavailable"
        new_status = "Available" if new_data.get('is_available') else "Unavailable"
        
        message = f"Availability change for {new_data.get('title', 'Unknown Product')}: " \
                  f"{old_status} → {new_status}"
        
        severity = "high" if not new_data.get('is_available') else "medium"
        
        self._create_alert(
            product_id=old_data.get('id'),
            alert_type="availability_change",
            message=message,
            severity=severity,
            metadata={
                'old_availability': old_data.get('is_available'),
                'new_availability': new_data.get('is_available'),
                'competitor': new_data.get('competitor')
            }
        )
    
    def _create_alert(self, product_id: int, alert_type: str, message: str, severity: str, metadata: Dict = None):
        """Create alert in database"""
        db = next(get_db())
        try:
            alert = Alert(
                product_id=product_id,
                alert_type=alert_type,
                message=message,
                severity=severity
            )
            
            if metadata:
                alert.set_metadata(metadata)
            
            db.add(alert)
            db.commit()
            
            # Send notification
            if settings.ENABLE_NOTIFICATIONS:
                self.notification_manager.send_alert(alert)
        
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
        finally:
            db.close()
    
    def _update_product_data(self, old_data: Dict, new_data: Dict):
        """Update product data in database"""
        db = next(get_db())
        try:
            # Update price history
            if new_data.get('price'):
                price_history = PriceHistory(
                    product_id=old_data['id'],
                    price=new_data['price'],
                    source="web_scraping"
                )
                db.add(price_history)
            
            # Update availability history
            availability_history = AvailabilityHistory(
                product_id=old_data['id'],
                is_available=new_data.get('is_available', False),
                availability_status=new_data.get('availability_status', 'unknown'),
                source="web_scraping"
            )
            db.add(availability_history)
            
            db.commit()
        
        except Exception as e:
            logger.error(f"Error updating product data: {e}")
        finally:
            db.close()
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle for all active products"""
        session = self.start_monitoring_session()
        
        try:
            db = next(get_db())
            
            # Get all active competitors
            competitors = db.query(Competitor).filter(Competitor.is_active == True).all()
            
            # Group products by competitor
            competitor_products = {}
            for competitor in competitors:
                products = db.query(Product).filter(
                    Product.competitor_id == competitor.id,
                    Product.is_active == True
                ).all()
                
                competitor_products[competitor.name] = [
                    {
                        'id': p.id,
                        'title': p.name,
                        'url': p.url,
                        'price': self._get_latest_price(p.id, db),
                        'is_available': self._get_latest_availability(p.id, db)
                    }
                    for p in products
                ]
            
            db.close()
            
            # Monitor each competitor
            total_results = {
                'session_id': session.id,
                'start_time': session.start_time,
                'competitors_monitored': len(competitors),
                'total_products': sum(len(products) for products in competitor_products.values()),
                'results': []
            }
            
            # Use ThreadPoolExecutor for concurrent monitoring
            futures = []
            for competitor_name, products in competitor_products.items():
                if products:  # Only monitor if there are products
                    future = self.executor.submit(self.monitor_competitor_products, competitor_name, products)
                    futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    total_results['results'].append(result)
                except Exception as e:
                    logger.error(f"Error in monitoring task: {e}")
                    total_results['results'].append({
                        'competitor': 'unknown',
                        'products_monitored': 0,
                        'successful_scrapes': 0,
                        'failed_scrapes': 0,
                        'price_changes': 0,
                        'availability_changes': 0,
                        'errors': [str(e)]
                    })
            
            # Update session statistics
            total_successful = sum(r['successful_scrapes'] for r in total_results['results'])
            total_failed = sum(r['failed_scrapes'] for r in total_results['results'])
            
            self.end_monitoring_session(
                session.id,
                status="completed",
                error_log=f"Successful: {total_successful}, Failed: {total_failed}"
            )
            
            logger.info(f"Monitoring cycle completed. Session: {session.id}")
            return total_results
        
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            self.end_monitoring_session(session.id, status="failed", error_log=str(e))
            return None
    
    def _get_latest_price(self, product_id: int, db: Session) -> Optional[float]:
        """Get the latest price for a product"""
        latest_price = db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id
        ).order_by(PriceHistory.timestamp.desc()).first()
        
        return latest_price.price if latest_price else None
    
    def _get_latest_availability(self, product_id: int, db: Session) -> Optional[bool]:
        """Get the latest availability for a product"""
        latest_availability = db.query(AvailabilityHistory).filter(
            AvailabilityHistory.product_id == product_id
        ).order_by(AvailabilityHistory.timestamp.desc()).first()
        
        return latest_availability.is_available if latest_availability else None
    
    def start_scheduled_monitoring(self):
        """Start scheduled monitoring"""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return
        
        self.is_running = True
        
        # Schedule monitoring every X minutes
        schedule.every(settings.MONITORING_INTERVAL_MINUTES).minutes.do(self.run_monitoring_cycle)
        
        logger.info(f"Started scheduled monitoring every {settings.MONITORING_INTERVAL_MINUTES} minutes")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Stopping scheduled monitoring...")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop scheduled monitoring"""
        self.is_running = False
        self.executor.shutdown(wait=True)
        logger.info("Monitoring stopped")
    
    def run_single_cycle(self):
        """Run a single monitoring cycle"""
        return self.run_monitoring_cycle()

# Initialize database
init_db()