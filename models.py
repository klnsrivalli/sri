from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional
from config import config

Base = declarative_base()

class Competitor(Base):
    __tablename__ = 'competitors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    base_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship to products
    products = relationship("Product", back_populates="competitor")

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    competitor_id = Column(Integer, ForeignKey('competitors.id'), nullable=False)
    name = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    sku = Column(String(100))
    category = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship to competitor and price history
    competitor = relationship("Competitor", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    availability = Column(String(50))
    rating = Column(Float)
    reviews_count = Column(Integer)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(Text)  # Store raw scraped data as JSON
    
    # Relationship to product
    product = relationship("Product", back_populates="price_history")

class PriceAlert(Base):
    __tablename__ = 'price_alerts'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # 'price_drop', 'price_increase', 'availability'
    threshold_value = Column(Float)
    threshold_percentage = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)

class ScrapingLog(Base):
    __tablename__ = 'scraping_logs'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'blocked'
    error_message = Column(Text)
    response_time = Column(Float)
    scraped_at = Column(DateTime, default=datetime.utcnow)

# Database setup
engine = create_engine(config.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with tables"""
    create_tables()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")