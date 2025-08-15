# E-commerce Competitor Monitoring Agent

A comprehensive Python-based solution for monitoring competitor prices, product availability, promotions, and market trends in real-time.

## Features

- **Multi-platform scraping**: Supports major e-commerce platforms (Amazon, eBay, Walmart, etc.)
- **Price tracking**: Monitor price changes and set alerts
- **Product availability**: Track stock levels and availability
- **Promotion monitoring**: Detect sales, discounts, and promotional campaigns
- **Data visualization**: Interactive dashboards with Plotly and Dash
- **Alert system**: Email and Telegram notifications
- **Database storage**: PostgreSQL integration for data persistence
- **API endpoints**: RESTful API for data access and management
- **Scheduling**: Automated monitoring with configurable intervals

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize database**:
   ```bash
   python scripts/init_db.py
   ```

4. **Start the monitoring agent**:
   ```bash
   python main.py
   ```

5. **Access the dashboard**:
   ```bash
   python dashboard.py
   # Open http://localhost:8050 in your browser
   ```

## Configuration

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/competitor_monitor

# API Keys
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Monitoring
MONITORING_INTERVAL=3600  # seconds
MAX_RETRIES=3
REQUEST_DELAY=2  # seconds between requests
```

## Project Structure

```
├── main.py                 # Main application entry point
├── config/                 # Configuration files
├── core/                   # Core monitoring logic
│   ├── scrapers/          # Platform-specific scrapers
│   ├── database/          # Database models and operations
│   └── alerts/            # Alert system
├── api/                   # FastAPI endpoints
├── dashboard/             # Dash web application
├── scripts/               # Utility scripts
└── tests/                 # Test files
```

## Usage Examples

### Adding a competitor product to monitor

```python
from core.database import DatabaseManager
from core.scrapers import AmazonScraper

# Initialize database
db = DatabaseManager()

# Add product to monitor
product_data = {
    "name": "iPhone 15 Pro",
    "url": "https://amazon.com/iphone-15-pro",
    "competitor": "Amazon",
    "category": "Electronics",
    "target_price": 999.99
}

db.add_product(product_data)
```

### Setting up price alerts

```python
from core.alerts import AlertManager

alert_manager = AlertManager()

# Set price drop alert
alert_manager.set_price_alert(
    product_id=1,
    threshold=899.99,
    alert_type="price_drop"
)
```

## API Endpoints

- `GET /api/products` - List all monitored products
- `POST /api/products` - Add new product to monitor
- `GET /api/products/{id}/history` - Get price history for a product
- `GET /api/competitors` - List competitor statistics
- `POST /api/alerts` - Configure alerts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details