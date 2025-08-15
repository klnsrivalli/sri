# E-commerce Competitor Monitoring Agent

A comprehensive Python-based system for monitoring competitor prices, availability, and product changes across major e-commerce platforms.

## 🚀 Features

- **Multi-Platform Monitoring**: Monitor Amazon, Walmart, Target, and other major e-commerce sites
- **Real-time Price Tracking**: Track price changes with configurable thresholds
- **Availability Monitoring**: Monitor product availability and stock status
- **Smart Notifications**: Email and Slack notifications for important changes
- **Web Dashboard**: Beautiful real-time dashboard with charts and analytics
- **REST API**: Full-featured API for integration with other systems
- **Database Storage**: SQLite/PostgreSQL support for historical data
- **Anti-Detection**: Advanced web scraping with proxy support and user agent rotation

## 📋 Requirements

- Python 3.8+
- Chrome/Chromium browser (for Selenium)
- Internet connection

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd e-commerce-competitor-monitor
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Chrome/Chromium** (if not already installed):
```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# macOS
brew install --cask google-chrome

# Windows
# Download from https://www.google.com/chrome/
```

4. **Setup environment variables** (optional):
```bash
cp .env.example .env
# Edit .env with your configuration
```

## ⚙️ Configuration

Create a `.env` file in the project root with your settings:

```env
# Database settings
DATABASE_URL=sqlite:///competitor_monitor.db

# API settings
API_HOST=0.0.0.0
API_PORT=8000

# Monitoring settings
MONITORING_INTERVAL_MINUTES=60
PRICE_CHANGE_THRESHOLD_PERCENT=5.0

# Notification settings
ENABLE_NOTIFICATIONS=True
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Proxy settings (optional)
USE_PROXY=False
PROXY_LIST=proxy1:port,proxy2:port
```

## 🚀 Quick Start

1. **Setup sample data**:
```bash
python main.py setup
```

2. **Start the API server**:
```bash
python main.py api
```

3. **Start the dashboard** (in another terminal):
```bash
python main.py dashboard
```

4. **Run monitoring** (in another terminal):
```bash
python main.py monitor
```

## 📊 Usage

### Command Line Interface

The system provides several commands:

```bash
# Run continuous monitoring
python main.py monitor

# Run API server
python main.py api

# Run web dashboard
python main.py dashboard

# Run single monitoring cycle
python main.py cycle

# Setup sample data
python main.py setup
```

### API Usage

The REST API provides endpoints for managing the monitoring system:

#### Competitors
```bash
# Get all competitors
GET /competitors/

# Create competitor
POST /competitors/
{
  "name": "Amazon",
  "base_url": "https://www.amazon.com",
  "is_active": true
}

# Get specific competitor
GET /competitors/{id}

# Update competitor
PUT /competitors/{id}

# Delete competitor
DELETE /competitors/{id}
```

#### Products
```bash
# Get all products
GET /products/

# Create product to monitor
POST /products/
{
  "competitor_id": 1,
  "name": "iPhone 13",
  "url": "https://www.amazon.com/iphone-13",
  "category": "Electronics",
  "brand": "Apple"
}

# Get product price history
GET /products/{id}/price-history?days=30

# Get product availability history
GET /products/{id}/availability-history?days=30
```

#### Monitoring Control
```bash
# Start scheduled monitoring
POST /monitor/start

# Stop monitoring
POST /monitor/stop

# Run single cycle
POST /monitor/run-cycle
```

#### Alerts
```bash
# Get alerts
GET /alerts/?is_read=false&severity=high

# Mark alert as read
PUT /alerts/{id}/read

# Get unread count
GET /alerts/unread-count
```

### Dashboard

Access the web dashboard at `http://localhost:8050` to view:

- **Overview**: Key metrics and statistics
- **Alerts**: Recent alerts and notifications
- **Competitors**: Comparison charts and analytics
- **Products**: Individual product monitoring with price/availability charts
- **Control**: Start/stop monitoring and run cycles

## 🔧 Advanced Configuration

### Adding New Competitors

To add support for new e-commerce sites, update the `COMPETITOR_CONFIGS` in `config.py`:

```python
COMPETITOR_CONFIGS = {
    "new_site": {
        "base_url": "https://www.newsite.com",
        "search_url": "https://www.newsite.com/search",
        "price_selectors": [
            "span.price",
            "div.product-price"
        ],
        "title_selectors": [
            "h1.product-title",
            "span.product-name"
        ],
        "availability_selectors": [
            "span.stock-status",
            "button.add-to-cart"
        ]
    }
}
```

### Custom Notifications

Extend the notification system in `notifications.py`:

```python
class CustomNotificationManager(NotificationManager):
    def send_custom_notification(self, alert):
        # Implement custom notification logic
        pass
```

### Database Configuration

For production use, configure PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/competitor_monitor
```

## 📈 Monitoring Features

### Price Monitoring
- Track price changes with configurable thresholds
- Historical price analysis
- Price trend visualization
- Alert on significant price drops/increases

### Availability Monitoring
- Monitor stock status changes
- Track product availability
- Alert when products go out of stock
- Monitor restocking events

### Competitor Analysis
- Compare prices across competitors
- Track market positioning
- Identify pricing strategies
- Monitor competitor product launches

## 🔒 Security & Best Practices

### Rate Limiting
- Built-in delays between requests
- Configurable monitoring intervals
- Respect for robots.txt

### Anti-Detection
- User agent rotation
- Proxy support
- Request randomization
- Selenium with stealth options

### Data Privacy
- Local data storage
- No data sent to third parties
- Configurable data retention

## 🐛 Troubleshooting

### Common Issues

1. **Chrome/Chromium not found**:
   ```bash
   # Install Chrome
   sudo apt-get install chromium-browser
   ```

2. **Permission denied errors**:
   ```bash
   # Make main.py executable
   chmod +x main.py
   ```

3. **Database errors**:
   ```bash
   # Reset database
   rm competitor_monitor.db
   python main.py setup
   ```

4. **Scraping blocked**:
   - Check if site is accessible
   - Verify selectors are correct
   - Try using proxies
   - Increase delays between requests

### Logs

Check the log file for detailed information:
```bash
tail -f competitor_monitor.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and legitimate business purposes only. Please respect website terms of service and robots.txt files. The authors are not responsible for any misuse of this software.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting section

## 🔄 Updates

Stay updated with the latest features:
```bash
git pull origin main
pip install -r requirements.txt
```