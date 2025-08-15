import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional
import logging

from config import config
from models import Product

logger = logging.getLogger(__name__)

class NotificationManager:
    """Handles sending notifications for price alerts and monitoring events"""
    
    def __init__(self):
        self.email_enabled = config.notifications.email_enabled
        self.smtp_server = config.notifications.smtp_server
        self.smtp_port = config.notifications.smtp_port
        self.email_user = config.notifications.email_user
        self.email_password = config.notifications.email_password
        self.recipients = config.notifications.recipients or []
    
    def send_email(self, subject: str, body: str, html_body: str = None) -> bool:
        """Send an email notification"""
        if not self.email_enabled or not self.recipients:
            logger.info("Email notifications disabled or no recipients configured")
            return False
        
        if not self.email_user or not self.email_password:
            logger.error("Email credentials not configured")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_user
            message["To"] = ", ".join(self.recipients)
            
            # Add text version
            text_part = MIMEText(body, "plain")
            message.attach(text_part)
            
            # Add HTML version if provided
            if html_body:
                html_part = MIMEText(html_body, "html")
                message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
                text = message.as_string()
                server.sendmail(self.email_user, self.recipients, text)
            
            logger.info(f"Email sent successfully to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_price_alert(self, product: Product, old_price: float, 
                        new_price: float, alert_type: str) -> bool:
        """Send a price change alert"""
        price_change = new_price - old_price
        price_change_pct = (price_change / old_price) * 100
        
        # Determine alert emoji and color
        if alert_type == 'price_drop':
            emoji = "📉"
            color = "#28a745"  # Green
            change_text = f"dropped by ${abs(price_change):.2f} ({abs(price_change_pct):.1f}%)"
        else:
            emoji = "📈"
            color = "#dc3545"  # Red
            change_text = f"increased by ${price_change:.2f} ({price_change_pct:.1f}%)"
        
        subject = f"{emoji} Price Alert: {product.name}"
        
        # Text version
        body = f"""
Price Alert - {product.competitor.name}

Product: {product.name}
Price has {change_text}

Previous Price: ${old_price:.2f}
Current Price: ${new_price:.2f}

Product URL: {product.url}

Alert triggered at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """.strip()
        
        # HTML version
        html_body = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid {color};">
                <h2 style="color: {color}; margin-top: 0;">{emoji} Price Alert</h2>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="margin-top: 0; color: #333;">{product.name}</h3>
                    <p><strong>Competitor:</strong> {product.competitor.name}</p>
                    <p><strong>Price has {change_text}</strong></p>
                    
                    <div style="display: flex; gap: 20px; margin: 15px 0;">
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Previous Price</div>
                            <div style="font-size: 18px; font-weight: bold;">${old_price:.2f}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Current Price</div>
                            <div style="font-size: 18px; font-weight: bold; color: {color};">${new_price:.2f}</div>
                        </div>
                    </div>
                    
                    <a href="{product.url}" style="display: inline-block; background-color: {color}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px;">View Product</a>
                </div>
                
                <p style="font-size: 12px; color: #666; margin-bottom: 0;">
                    Alert triggered at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(subject, body, html_body)
    
    def send_monitoring_summary(self, stats: dict) -> bool:
        """Send a monitoring summary report"""
        subject = f"📊 Competitor Monitoring Summary - {datetime.utcnow().strftime('%Y-%m-%d')}"
        
        # Text version
        body = f"""
Daily Competitor Monitoring Summary

Total Products Monitored: {stats.get('total_products', 0)}
Successful Scrapes: {stats.get('successful_scrapes', 0)}
Failed Scrapes: {stats.get('failed_scrapes', 0)}
Price Changes Detected: {stats.get('price_changes', 0)}
Alerts Triggered: {stats.get('alerts_triggered', 0)}
Success Rate: {stats.get('success_rate', 0):.1f}%

Report generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """.strip()
        
        # HTML version
        success_color = "#28a745" if stats.get('success_rate', 0) >= 80 else "#ffc107" if stats.get('success_rate', 0) >= 60 else "#dc3545"
        
        html_body = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; margin-top: 0;">📊 Competitor Monitoring Summary</h2>
                <p style="color: #666;">{datetime.utcnow().strftime('%Y-%m-%d')}</p>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                    <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #e9ecef;">
                        <div style="font-size: 24px; font-weight: bold; color: #007bff;">{stats.get('total_products', 0)}</div>
                        <div style="font-size: 12px; color: #666;">Total Products</div>
                    </div>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #e9ecef;">
                        <div style="font-size: 24px; font-weight: bold; color: #28a745;">{stats.get('successful_scrapes', 0)}</div>
                        <div style="font-size: 12px; color: #666;">Successful Scrapes</div>
                    </div>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #e9ecef;">
                        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">{stats.get('failed_scrapes', 0)}</div>
                        <div style="font-size: 12px; color: #666;">Failed Scrapes</div>
                    </div>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #e9ecef;">
                        <div style="font-size: 24px; font-weight: bold; color: #ffc107;">{stats.get('price_changes', 0)}</div>
                        <div style="font-size: 12px; color: #666;">Price Changes</div>
                    </div>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #e9ecef;">
                        <div style="font-size: 24px; font-weight: bold; color: #17a2b8;">{stats.get('alerts_triggered', 0)}</div>
                        <div style="font-size: 12px; color: #666;">Alerts Triggered</div>
                    </div>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #e9ecef;">
                        <div style="font-size: 24px; font-weight: bold; color: {success_color};">{stats.get('success_rate', 0):.1f}%</div>
                        <div style="font-size: 12px; color: #666;">Success Rate</div>
                    </div>
                </div>
                
                <p style="font-size: 12px; color: #666; margin-bottom: 0; text-align: center;">
                    Report generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(subject, body, html_body)
    
    def send_error_alert(self, error_message: str, context: str = "") -> bool:
        """Send an error alert notification"""
        subject = "🚨 Competitor Monitoring Error Alert"
        
        # Text version
        body = f"""
Error Alert - Competitor Monitoring System

An error occurred in the competitor monitoring system:

Error: {error_message}
Context: {context}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please check the system logs for more details.
        """.strip()
        
        # HTML version
        html_body = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #f8d7da; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545;">
                <h2 style="color: #721c24; margin-top: 0;">🚨 Error Alert</h2>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="margin-top: 0; color: #333;">Competitor Monitoring System Error</h3>
                    
                    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0;">
                        <strong>Error:</strong> {error_message}
                    </div>
                    
                    {f'<div style="background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0;"><strong>Context:</strong> {context}</div>' if context else ''}
                    
                    <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    
                    <p style="color: #666; font-style: italic;">
                        Please check the system logs for more details and take appropriate action.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(subject, body, html_body)
    
    def test_email_connection(self) -> bool:
        """Test the email connection and configuration"""
        if not self.email_enabled:
            logger.info("Email notifications are disabled")
            return False
        
        if not self.email_user or not self.email_password:
            logger.error("Email credentials not configured")
            return False
        
        if not self.recipients:
            logger.error("No email recipients configured")
            return False
        
        try:
            # Test SMTP connection
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
            
            logger.info("Email connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Email connection test failed: {str(e)}")
            return False
    
    def send_test_notification(self) -> bool:
        """Send a test notification to verify the system is working"""
        subject = "✅ Test Notification - Competitor Monitoring System"
        
        body = f"""
Test Notification

This is a test notification from your competitor monitoring system.

If you receive this email, your notification system is working correctly.

Test sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """.strip()
        
        html_body = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #d4edda; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                <h2 style="color: #155724; margin-top: 0;">✅ Test Notification</h2>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="margin-top: 0; color: #333;">Competitor Monitoring System</h3>
                    
                    <p>This is a test notification from your competitor monitoring system.</p>
                    
                    <p style="color: #28a745; font-weight: bold;">
                        ✅ If you receive this email, your notification system is working correctly.
                    </p>
                    
                    <p style="font-size: 12px; color: #666;">
                        Test sent at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(subject, body, html_body)