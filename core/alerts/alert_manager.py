import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio

from config.settings import settings
from core.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

class AlertManager:
    """Manages alerts for price changes, stock changes, and promotions."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.alert_templates = {
            'price_drop': {
                'subject': 'Price Drop Alert: {product_name}',
                'body': '''
Price Drop Alert!

Product: {product_name}
Competitor: {competitor}
Old Price: ${old_price:.2f}
New Price: ${new_price:.2f}
Price Change: ${price_change:.2f} ({percentage_change:.1f}%)
URL: {url}

This is an automated alert from your competitor monitoring system.
                ''',
                'telegram': '''
🚨 Price Drop Alert!

📦 Product: {product_name}
🏪 Competitor: {competitor}
💰 Old Price: ${old_price:.2f}
💸 New Price: ${new_price:.2f}
📉 Change: ${price_change:.2f} ({percentage_change:.1f}%)
🔗 URL: {url}
                '''
            },
            'price_increase': {
                'subject': 'Price Increase Alert: {product_name}',
                'body': '''
Price Increase Alert!

Product: {product_name}
Competitor: {competitor}
Old Price: ${old_price:.2f}
New Price: ${new_price:.2f}
Price Change: ${price_change:.2f} ({percentage_change:.1f}%)
URL: {url}

This is an automated alert from your competitor monitoring system.
                ''',
                'telegram': '''
📈 Price Increase Alert!

📦 Product: {product_name}
🏪 Competitor: {competitor}
💰 Old Price: ${old_price:.2f}
💸 New Price: ${new_price:.2f}
📈 Change: ${price_change:.2f} ({percentage_change:.1f}%)
🔗 URL: {url}
                '''
            },
            'stock_change': {
                'subject': 'Stock Status Change: {product_name}',
                'body': '''
Stock Status Change Alert!

Product: {product_name}
Competitor: {competitor}
Previous Status: {old_status}
New Status: {new_status}
URL: {url}

This is an automated alert from your competitor monitoring system.
                ''',
                'telegram': '''
📦 Stock Status Change!

📦 Product: {product_name}
🏪 Competitor: {competitor}
📊 Previous: {old_status}
📊 Current: {new_status}
🔗 URL: {url}
                '''
            },
            'promotion': {
                'subject': 'New Promotion Alert: {product_name}',
                'body': '''
New Promotion Alert!

Product: {product_name}
Competitor: {competitor}
Current Price: ${current_price:.2f}
Promotion: {promotion_text}
URL: {url}

This is an automated alert from your competitor monitoring system.
                ''',
                'telegram': '''
🎉 New Promotion Alert!

📦 Product: {product_name}
🏪 Competitor: {competitor}
💰 Price: ${current_price:.2f}
🎯 Promotion: {promotion_text}
🔗 URL: {url}
                '''
            }
        }
    
    def check_price_alerts(self, product_id: int, new_price: float, old_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """Check if price changes trigger any alerts."""
        if old_price is None:
            # Get the previous price from database
            latest_price = self.db.get_latest_price(product_id)
            if latest_price:
                old_price = latest_price.price
            else:
                return []  # No previous price to compare
        
        if old_price == new_price:
            return []  # No price change
        
        alerts_triggered = []
        product = self.db.get_product(product_id)
        if not product:
            return []
        
        # Calculate price change
        price_change = new_price - old_price
        percentage_change = (price_change / old_price) * 100
        
        # Check configured alerts
        product_alerts = self.db.get_alerts(product_id=product_id, active_only=True)
        
        for alert in product_alerts:
            if alert.alert_type == 'price_drop' and price_change < 0:
                if alert.threshold is None or abs(percentage_change) >= alert.threshold:
                    alert_data = self._create_price_alert_data(
                        alert_type='price_drop',
                        product=product,
                        old_price=old_price,
                        new_price=new_price,
                        price_change=price_change,
                        percentage_change=percentage_change
                    )
                    alerts_triggered.append(alert_data)
                    
            elif alert.alert_type == 'price_increase' and price_change > 0:
                if alert.threshold is None or abs(percentage_change) >= alert.threshold:
                    alert_data = self._create_price_alert_data(
                        alert_type='price_increase',
                        product=product,
                        old_price=old_price,
                        new_price=new_price,
                        price_change=price_change,
                        percentage_change=percentage_change
                    )
                    alerts_triggered.append(alert_data)
        
        return alerts_triggered
    
    def check_stock_alerts(self, product_id: int, new_status: str, old_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check if stock status changes trigger any alerts."""
        if old_status == new_status:
            return []  # No status change
        
        alerts_triggered = []
        product = self.db.get_product(product_id)
        if not product:
            return []
        
        # Check configured alerts
        product_alerts = self.db.get_alerts(product_id=product_id, active_only=True)
        
        for alert in product_alerts:
            if alert.alert_type == 'stock_change':
                alert_data = self._create_stock_alert_data(
                    product=product,
                    old_status=old_status or 'unknown',
                    new_status=new_status
                )
                alerts_triggered.append(alert_data)
        
        return alerts_triggered
    
    def check_promotion_alerts(self, product_id: int, promotion_text: Optional[str]) -> List[Dict[str, Any]]:
        """Check if new promotions trigger any alerts."""
        if not promotion_text:
            return []  # No promotion
        
        alerts_triggered = []
        product = self.db.get_product(product_id)
        if not product:
            return []
        
        # Get current price for the alert
        latest_price = self.db.get_latest_price(product_id)
        current_price = latest_price.price if latest_price else 0.0
        
        # Check configured alerts
        product_alerts = self.db.get_alerts(product_id=product_id, active_only=True)
        
        for alert in product_alerts:
            if alert.alert_type == 'promotion':
                alert_data = self._create_promotion_alert_data(
                    product=product,
                    current_price=current_price,
                    promotion_text=promotion_text
                )
                alerts_triggered.append(alert_data)
        
        return alerts_triggered
    
    def _create_price_alert_data(self, alert_type: str, product, old_price: float, 
                                new_price: float, price_change: float, percentage_change: float) -> Dict[str, Any]:
        """Create price alert data."""
        template = self.alert_templates[alert_type]
        
        return {
            'type': alert_type,
            'product_id': product.id,
            'product_name': product.name,
            'competitor': product.competitor,
            'old_price': old_price,
            'new_price': new_price,
            'price_change': price_change,
            'percentage_change': percentage_change,
            'url': product.url,
            'email_subject': template['subject'].format(product_name=product.name),
            'email_body': template['body'].format(
                product_name=product.name,
                competitor=product.competitor,
                old_price=old_price,
                new_price=new_price,
                price_change=price_change,
                percentage_change=percentage_change,
                url=product.url
            ),
            'telegram_message': template['telegram'].format(
                product_name=product.name,
                competitor=product.competitor,
                old_price=old_price,
                new_price=new_price,
                price_change=price_change,
                percentage_change=percentage_change,
                url=product.url
            )
        }
    
    def _create_stock_alert_data(self, product, old_status: str, new_status: str) -> Dict[str, Any]:
        """Create stock alert data."""
        template = self.alert_templates['stock_change']
        
        return {
            'type': 'stock_change',
            'product_id': product.id,
            'product_name': product.name,
            'competitor': product.competitor,
            'old_status': old_status,
            'new_status': new_status,
            'url': product.url,
            'email_subject': template['subject'].format(product_name=product.name),
            'email_body': template['body'].format(
                product_name=product.name,
                competitor=product.competitor,
                old_status=old_status,
                new_status=new_status,
                url=product.url
            ),
            'telegram_message': template['telegram'].format(
                product_name=product.name,
                competitor=product.competitor,
                old_status=old_status,
                new_status=new_status,
                url=product.url
            )
        }
    
    def _create_promotion_alert_data(self, product, current_price: float, promotion_text: str) -> Dict[str, Any]:
        """Create promotion alert data."""
        template = self.alert_templates['promotion']
        
        return {
            'type': 'promotion',
            'product_id': product.id,
            'product_name': product.name,
            'competitor': product.competitor,
            'current_price': current_price,
            'promotion_text': promotion_text,
            'url': product.url,
            'email_subject': template['subject'].format(product_name=product.name),
            'email_body': template['body'].format(
                product_name=product.name,
                competitor=product.competitor,
                current_price=current_price,
                promotion_text=promotion_text,
                url=product.url
            ),
            'telegram_message': template['telegram'].format(
                product_name=product.name,
                competitor=product.competitor,
                current_price=current_price,
                promotion_text=promotion_text,
                url=product.url
            )
        }
    
    def send_email_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send email alert."""
        if not settings.EMAIL_USER or not settings.EMAIL_PASSWORD:
            logger.warning("Email credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_USER
            msg['To'] = settings.EMAIL_USER  # Send to self for now
            msg['Subject'] = alert_data['email_subject']
            
            msg.attach(MIMEText(alert_data['email_body'], 'plain'))
            
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {alert_data['product_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    async def send_telegram_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send Telegram alert."""
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            logger.warning("Telegram credentials not configured")
            return False
        
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': settings.TELEGRAM_CHAT_ID,
                'text': alert_data['telegram_message'],
                'parse_mode': 'HTML'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info(f"Telegram alert sent for {alert_data['product_name']}")
                        return True
                    else:
                        logger.error(f"Telegram API error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def send_alerts(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Send multiple alerts via email and Telegram."""
        results = {'email_sent': 0, 'email_failed': 0, 'telegram_sent': 0, 'telegram_failed': 0}
        
        for alert_data in alerts:
            # Send email alert
            if self.send_email_alert(alert_data):
                results['email_sent'] += 1
            else:
                results['email_failed'] += 1
            
            # Send Telegram alert
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create new event loop for async operation
                    import threading
                    def send_telegram():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            new_loop.run_until_complete(self.send_telegram_alert(alert_data))
                        finally:
                            new_loop.close()
                    
                    thread = threading.Thread(target=send_telegram)
                    thread.start()
                    thread.join()
                else:
                    loop.run_until_complete(self.send_telegram_alert(alert_data))
                results['telegram_sent'] += 1
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")
                results['telegram_failed'] += 1
        
        return results