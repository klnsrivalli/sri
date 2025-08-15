from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from .models import Base, Product, PriceHistory, Alert, Competitor, MonitoringSession
from config.settings import settings

class DatabaseManager:
    """Database manager for handling all database operations."""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
        
    # Product operations
    def add_product(self, product_data: Dict[str, Any]) -> Product:
        """Add a new product to monitor."""
        with self.get_session() as session:
            product = Product(**product_data)
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
            
    def get_product(self, product_id: int) -> Optional[Product]:
        """Get a product by ID."""
        with self.get_session() as session:
            return session.query(Product).filter(Product.id == product_id).first()
            
    def get_products(self, active_only: bool = True) -> List[Product]:
        """Get all products, optionally filtered by active status."""
        with self.get_session() as session:
            query = session.query(Product)
            if active_only:
                query = query.filter(Product.is_active == True)
            return query.all()
            
    def update_product(self, product_id: int, update_data: Dict[str, Any]) -> Optional[Product]:
        """Update a product."""
        with self.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                for key, value in update_data.items():
                    setattr(product, key, value)
                product.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(product)
            return product
            
    def delete_product(self, product_id: int) -> bool:
        """Delete a product."""
        with self.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                session.delete(product)
                session.commit()
                return True
            return False
            
    # Price history operations
    def add_price_history(self, price_data: Dict[str, Any]) -> PriceHistory:
        """Add a new price history entry."""
        with self.get_session() as session:
            price_history = PriceHistory(**price_data)
            session.add(price_history)
            session.commit()
            session.refresh(price_history)
            return price_history
            
    def get_price_history(self, product_id: int, days: int = 30) -> List[PriceHistory]:
        """Get price history for a product within specified days."""
        with self.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return session.query(PriceHistory).filter(
                and_(
                    PriceHistory.product_id == product_id,
                    PriceHistory.timestamp >= cutoff_date
                )
            ).order_by(PriceHistory.timestamp.desc()).all()
            
    def get_latest_price(self, product_id: int) -> Optional[PriceHistory]:
        """Get the latest price for a product."""
        with self.get_session() as session:
            return session.query(PriceHistory).filter(
                PriceHistory.product_id == product_id
            ).order_by(PriceHistory.timestamp.desc()).first()
            
    # Alert operations
    def add_alert(self, alert_data: Dict[str, Any]) -> Alert:
        """Add a new alert configuration."""
        with self.get_session() as session:
            alert = Alert(**alert_data)
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return alert
            
    def get_alerts(self, product_id: Optional[int] = None, active_only: bool = True) -> List[Alert]:
        """Get alerts, optionally filtered by product and active status."""
        with self.get_session() as session:
            query = session.query(Alert)
            if product_id:
                query = query.filter(Alert.product_id == product_id)
            if active_only:
                query = query.filter(Alert.is_active == True)
            return query.all()
            
    def update_alert(self, alert_id: int, update_data: Dict[str, Any]) -> Optional[Alert]:
        """Update an alert configuration."""
        with self.get_session() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                for key, value in update_data.items():
                    setattr(alert, key, value)
                session.commit()
                session.refresh(alert)
            return alert
            
    # Competitor operations
    def add_competitor(self, competitor_data: Dict[str, Any]) -> Competitor:
        """Add a new competitor."""
        with self.get_session() as session:
            competitor = Competitor(**competitor_data)
            session.add(competitor)
            session.commit()
            session.refresh(competitor)
            return competitor
            
    def get_competitors(self, active_only: bool = True) -> List[Competitor]:
        """Get all competitors, optionally filtered by active status."""
        with self.get_session() as session:
            query = session.query(Competitor)
            if active_only:
                query = query.filter(Competitor.is_active == True)
            return query.all()
            
    # Monitoring session operations
    def start_monitoring_session(self) -> MonitoringSession:
        """Start a new monitoring session."""
        with self.get_session() as session:
            monitoring_session = MonitoringSession()
            session.add(monitoring_session)
            session.commit()
            session.refresh(monitoring_session)
            return monitoring_session
            
    def complete_monitoring_session(self, session_id: int, **kwargs) -> Optional[MonitoringSession]:
        """Complete a monitoring session with results."""
        with self.get_session() as session:
            monitoring_session = session.query(MonitoringSession).filter(
                MonitoringSession.id == session_id
            ).first()
            if monitoring_session:
                monitoring_session.completed_at = datetime.utcnow()
                monitoring_session.status = "completed"
                for key, value in kwargs.items():
                    if hasattr(monitoring_session, key):
                        setattr(monitoring_session, key, value)
                session.commit()
                session.refresh(monitoring_session)
            return monitoring_session
            
    # Analytics methods
    def get_price_statistics(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """Get price statistics for a product."""
        with self.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            prices = session.query(PriceHistory.price).filter(
                and_(
                    PriceHistory.product_id == product_id,
                    PriceHistory.timestamp >= cutoff_date
                )
            ).all()
            
            if not prices:
                return {}
                
            price_list = [p[0] for p in prices]
            return {
                "min_price": min(price_list),
                "max_price": max(price_list),
                "avg_price": sum(price_list) / len(price_list),
                "price_count": len(price_list),
                "latest_price": price_list[0] if price_list else None
            }
            
    def get_competitor_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all competitors."""
        with self.get_session() as session:
            competitors = session.query(Competitor).filter(Competitor.is_active == True).all()
            products_per_competitor = {}
            
            for competitor in competitors:
                product_count = session.query(Product).filter(
                    and_(
                        Product.competitor == competitor.name,
                        Product.is_active == True
                    )
                ).count()
                products_per_competitor[competitor.name] = product_count
                
            return {
                "total_competitors": len(competitors),
                "total_products": sum(products_per_competitor.values()),
                "products_per_competitor": products_per_competitor
            }