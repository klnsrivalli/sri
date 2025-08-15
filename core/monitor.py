import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from core.database.manager import DatabaseManager
from core.scrapers import get_scraper_for_url
from core.alerts.alert_manager import AlertManager
from config.settings import settings

logger = logging.getLogger(__name__)

class CompetitorMonitor:
    """Main monitoring engine for competitor price tracking."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.alert_manager = AlertManager()
        self.is_running = False
        self.monitoring_thread = None
        
    def start_monitoring(self, interval: Optional[int] = None):
        """Start the monitoring process in a separate thread."""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return
        
        self.is_running = True
        interval = interval or settings.MONITORING_INTERVAL
        
        def monitoring_loop():
            while self.is_running:
                try:
                    logger.info("Starting monitoring cycle")
                    self.run_monitoring_cycle()
                    logger.info(f"Monitoring cycle completed. Waiting {interval} seconds...")
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Competitor monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Competitor monitoring stopped")
    
    def run_monitoring_cycle(self):
        """Run a single monitoring cycle for all products."""
        # Start monitoring session
        session = self.db.start_monitoring_session()
        
        try:
            # Get all active products
            products = self.db.get_products(active_only=True)
            logger.info(f"Monitoring {len(products)} products")
            
            if not products:
                logger.info("No products to monitor")
                return
            
            # Process products in parallel
            results = self._process_products_parallel(products)
            
            # Update session with results
            processed_count = len(results)
            updated_count = sum(1 for r in results if r.get('updated', False))
            error_count = sum(1 for r in results if r.get('error', False))
            
            self.db.complete_monitoring_session(
                session_id=session.id,
                products_processed=processed_count,
                products_updated=updated_count,
                errors_count=error_count,
                status='completed'
            )
            
            logger.info(f"Monitoring cycle completed: {updated_count} updated, {error_count} errors")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            self.db.complete_monitoring_session(
                session_id=session.id,
                status='failed',
                error_log=str(e)
            )
    
    def _process_products_parallel(self, products: List) -> List[Dict[str, Any]]:
        """Process products in parallel using ThreadPoolExecutor."""
        results = []
        
        # Use a reasonable number of workers to avoid overwhelming servers
        max_workers = min(10, len(products))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all products for processing
            future_to_product = {
                executor.submit(self._process_single_product, product): product 
                for product in products
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_product):
                product = future_to_product[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing product {product.id}: {e}")
                    results.append({
                        'product_id': product.id,
                        'updated': False,
                        'error': True,
                        'error_message': str(e)
                    })
        
        return results
    
    def _process_single_product(self, product) -> Dict[str, Any]:
        """Process a single product: scrape, update database, and check alerts."""
        try:
            logger.debug(f"Processing product {product.id}: {product.name}")
            
            # Get appropriate scraper for the product URL
            scraper = get_scraper_for_url(product.url)
            
            # Scrape product information
            scraped_data = scraper.scrape_product(product.url)
            
            if not scraped_data:
                return {
                    'product_id': product.id,
                    'updated': False,
                    'error': True,
                    'error_message': 'Failed to scrape product data'
                }
            
            # Get previous price for comparison
            previous_price = self.db.get_latest_price(product.id)
            previous_price_value = previous_price.price if previous_price else None
            previous_stock_status = previous_price.stock_status if previous_price else None
            
            # Prepare price history data
            price_data = {
                'product_id': product.id,
                'price': scraped_data.get('price'),
                'currency': scraped_data.get('currency', 'USD'),
                'is_available': scraped_data.get('is_available', True),
                'stock_status': scraped_data.get('stock_status', 'unknown'),
                'promotion_text': scraped_data.get('promotion_text'),
                'shipping_cost': scraped_data.get('shipping_cost'),
                'rating': scraped_data.get('rating'),
                'review_count': scraped_data.get('review_count')
            }
            
            # Add price history entry
            price_history = self.db.add_price_history(price_data)
            
            # Check for alerts
            alerts_triggered = []
            
            # Check price alerts
            if scraped_data.get('price') and previous_price_value:
                price_alerts = self.alert_manager.check_price_alerts(
                    product.id, 
                    scraped_data['price'], 
                    previous_price_value
                )
                alerts_triggered.extend(price_alerts)
            
            # Check stock alerts
            if scraped_data.get('stock_status'):
                stock_alerts = self.alert_manager.check_stock_alerts(
                    product.id,
                    scraped_data['stock_status'],
                    previous_stock_status
                )
                alerts_triggered.extend(stock_alerts)
            
            # Check promotion alerts
            if scraped_data.get('promotion_text'):
                promotion_alerts = self.alert_manager.check_promotion_alerts(
                    product.id,
                    scraped_data['promotion_text']
                )
                alerts_triggered.extend(promotion_alerts)
            
            # Send alerts if any were triggered
            if alerts_triggered:
                alert_results = self.alert_manager.send_alerts(alerts_triggered)
                logger.info(f"Sent {len(alerts_triggered)} alerts for product {product.id}")
            
            return {
                'product_id': product.id,
                'updated': True,
                'error': False,
                'price': scraped_data.get('price'),
                'alerts_triggered': len(alerts_triggered)
            }
            
        except Exception as e:
            logger.error(f"Error processing product {product.id}: {e}")
            return {
                'product_id': product.id,
                'updated': False,
                'error': True,
                'error_message': str(e)
            }
    
    def add_product_to_monitor(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new product to monitor."""
        try:
            # Validate required fields
            required_fields = ['name', 'url', 'competitor']
            for field in required_fields:
                if field not in product_data:
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Add product to database
            product = self.db.add_product(product_data)
            
            # Set up default alerts
            self._setup_default_alerts(product.id)
            
            logger.info(f"Added product to monitor: {product.name}")
            return {'success': True, 'product_id': product.id}
            
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return {'success': False, 'error': str(e)}
    
    def _setup_default_alerts(self, product_id: int):
        """Set up default alerts for a new product."""
        default_alerts = [
            {
                'product_id': product_id,
                'alert_type': 'price_drop',
                'threshold': settings.PRICE_CHANGE_THRESHOLD * 100  # Convert to percentage
            },
            {
                'product_id': product_id,
                'alert_type': 'stock_change',
                'threshold': None
            }
        ]
        
        for alert_data in default_alerts:
            try:
                self.db.add_alert(alert_data)
            except Exception as e:
                logger.error(f"Error setting up default alert: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'is_running': self.is_running,
            'total_products': len(self.db.get_products(active_only=True)),
            'total_competitors': len(self.db.get_competitors(active_only=True)),
            'last_session': self._get_last_session_info()
        }
    
    def _get_last_session_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the last monitoring session."""
        try:
            with self.db.get_session() as session:
                from core.database.models import MonitoringSession
                last_session = session.query(MonitoringSession).order_by(
                    MonitoringSession.started_at.desc()
                ).first()
                
                if last_session:
                    return {
                        'started_at': last_session.started_at.isoformat(),
                        'completed_at': last_session.completed_at.isoformat() if last_session.completed_at else None,
                        'status': last_session.status,
                        'products_processed': last_session.products_processed,
                        'products_updated': last_session.products_updated,
                        'errors_count': last_session.errors_count
                    }
        except Exception as e:
            logger.error(f"Error getting last session info: {e}")
        
        return None
    
    def get_product_statistics(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """Get statistics for a specific product."""
        try:
            stats = self.db.get_price_statistics(product_id, days)
            price_history = self.db.get_price_history(product_id, days)
            
            return {
                'statistics': stats,
                'price_history': [
                    {
                        'price': ph.price,
                        'timestamp': ph.timestamp.isoformat(),
                        'is_available': ph.is_available,
                        'stock_status': ph.stock_status
                    }
                    for ph in price_history
                ]
            }
        except Exception as e:
            logger.error(f"Error getting product statistics: {e}")
            return {}
    
    def get_competitor_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all competitors."""
        try:
            return self.db.get_competitor_summary()
        except Exception as e:
            logger.error(f"Error getting competitor summary: {e}")
            return {}