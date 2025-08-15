# E-commerce Competitor Monitoring Agent 🛒📊

A comprehensive, production-ready tool for monitoring competitor prices, tracking changes, and generating actionable insights for e-commerce businesses.

## 🚀 Features

### Core Functionality
- **Multi-platform scraping** with requests/BeautifulSoup and Selenium support
- **Real-time price monitoring** with configurable intervals
- **Intelligent price change detection** with customizable thresholds
- **Comprehensive alerting system** via email notifications
- **Rich data visualization** with interactive charts and dashboards
- **Historical price tracking** with trend analysis
- **Competitor comparison** across similar products

### Technical Highlights
- **Robust architecture** with SQLite/PostgreSQL database support
- **Anti-bot detection handling** with randomized user agents and delays
- **Concurrent scraping** for improved performance
- **Rate limiting** to respect website policies
- **Error handling and retry logic** for reliable operation
- **CLI interface** for easy management and automation
- **Scheduling system** for automated monitoring

## 📋 Requirements

- Python 3.8+
- Chrome browser (for Selenium scraping)
- SMTP server access (for email notifications)

## 🔧 Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd competitor-monitoring-agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Initialize the system**
```bash
python cli.py init
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=sqlite:///competitor_monitoring.db

# Email Notifications
EMAIL_ENABLED=true
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENTS=recipient1@email.com,recipient2@email.com

# Monitoring Settings
CHECK_INTERVAL=3600
PRICE_CHANGE_THRESHOLD=0.05
MAX_RETRIES=3
TIMEOUT=30
```

### Email Setup

For Gmail:
1. Enable 2-factor authentication
2. Generate an app password
3. Use the app password in `EMAIL_PASSWORD`

## 🚀 Quick Start

### 1. Add a Competitor

```bash
# Add Amazon as a competitor with custom selectors
python cli.py competitor add "Amazon" "https://www.amazon.com" \
  --selectors '{"price": ".a-price .a-offscreen", "title": "#productTitle", "availability": "#availability span"}'

# List all competitors
python cli.py competitor list
```

### 2. Add Products to Monitor

```bash
# Add a product to monitor
python cli.py product add "Amazon" "iPhone 15 Pro" \
  "https://www.amazon.com/dp/B0CHX1W5Y4" \
  --sku "IPHONE15PRO" --category "Electronics"

# List all products
python cli.py product list
```

### 3. Test Product Scraping

```bash
# Test scraping a specific product
python cli.py product test 1

# Test with Selenium (for dynamic content)
python cli.py product test 1 --selenium
```

### 4. Run Monitoring

```bash
# Run one-time monitoring
python cli.py monitor run

# Run with notifications
python cli.py monitor run --notify

# Schedule automatic monitoring (every hour)
python cli.py monitor schedule-monitoring --interval 3600
```

### 5. Set Up Price Alerts

```bash
# Alert when price drops by 10%
python cli.py alert add 1 price_drop --threshold-percentage 10

# Alert when price goes below $800
python cli.py alert add 1 price_drop --threshold-value 800
```

### 6. Generate Reports

```bash
# Create price history chart
python cli.py report price-history 1 --days 30

# Compare competitors for iPhone products
python cli.py report compare "iPhone"

# Generate trend analysis
python cli.py report trends --days 30

# Create monitoring dashboard
python cli.py report dashboard

# Generate summary report
python cli.py report summary --days 7
```

## 📊 Data Models

### Competitors
- Name, base URL, creation date
- Custom CSS selectors for data extraction
- Active/inactive status

### Products
- Name, URL, SKU, category
- Associated competitor
- Active/inactive status

### Price History
- Historical price data with timestamps
- Currency, availability status
- Product ratings and review counts
- Raw scraped data for debugging

### Price Alerts
- Configurable threshold-based alerts
- Support for percentage and absolute value triggers
- Email notifications for price changes

### Scraping Logs
- Success/failure tracking
- Error messages and response times
- Performance monitoring

## 🔍 Advanced Usage

### Custom CSS Selectors

When adding competitors, customize CSS selectors for accurate data extraction:

```bash
python cli.py competitor add "Target" "https://www.target.com" \
  --selectors '{
    "price": "[data-test=\"product-price\"]",
    "title": "[data-test=\"product-title\"]",
    "availability": "[data-test=\"stockStatus\"]",
    "rating": "[data-test=\"ratings-reviews\"]"
  }'
```

### Selenium Scraping

For sites with dynamic content, use Selenium:

```bash
# Run monitoring with Selenium
python cli.py monitor run --selenium

# Test specific product with Selenium
python cli.py product test 1 --selenium
```

### Scheduling Options

```bash
# Check every 30 minutes
python cli.py monitor schedule-monitoring --interval 1800

# Use Selenium for scheduled monitoring
python cli.py monitor schedule-monitoring --interval 3600 --selenium
```

### Report Formats

```bash
# JSON format for API integration
python cli.py report summary --format json --days 7

# Text format for human reading
python cli.py report summary --format text --days 7
```

## 📈 Visualization Features

### Interactive Charts
- **Price History Charts**: Track price changes over time
- **Competitor Comparison**: Side-by-side price comparisons
- **Trend Analysis**: Multi-product trend visualization
- **Monitoring Dashboard**: Real-time system overview

### Report Types
- **Summary Reports**: Key metrics and insights
- **Price Change Analysis**: Biggest increases/decreases
- **Competitor Performance**: Average prices and product counts
- **System Statistics**: Success rates and monitoring health

## 🔧 Technical Architecture

### Components

1. **Config System** (`config.py`): Centralized configuration management
2. **Data Models** (`models.py`): SQLAlchemy database models
3. **Scraping Engine** (`scraper.py`): Multi-method web scraping
4. **Monitoring Core** (`monitor.py`): Price tracking and alerts
5. **Notifications** (`notifications.py`): Email alert system
6. **Visualizations** (`visualizations.py`): Chart and report generation
7. **CLI Interface** (`cli.py`): Command-line management

### Database Schema

```sql
-- Competitors table
CREATE TABLE competitors (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    created_at DATETIME,
    is_active BOOLEAN
);

-- Products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    competitor_id INTEGER,
    name VARCHAR(500) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    sku VARCHAR(100),
    category VARCHAR(200),
    created_at DATETIME,
    is_active BOOLEAN
);

-- Price history table
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY,
    product_id INTEGER,
    price FLOAT NOT NULL,
    currency VARCHAR(10),
    availability VARCHAR(50),
    rating FLOAT,
    reviews_count INTEGER,
    scraped_at DATETIME,
    raw_data TEXT
);
```

## 🛡️ Best Practices

### Scraping Ethics
- Respect robots.txt files
- Use appropriate delays between requests
- Don't overload target servers
- Monitor for rate limiting and adapt accordingly

### Data Quality
- Regularly validate CSS selectors
- Monitor scraping success rates
- Review and clean historical data
- Test selectors after website updates

### Performance Optimization
- Use requests for static content
- Reserve Selenium for dynamic content only
- Implement connection pooling
- Cache frequently accessed data

### Security
- Store credentials in environment variables
- Use app passwords for email authentication
- Regularly rotate access credentials
- Monitor for unauthorized access

## 🔍 Troubleshooting

### Common Issues

**Scraping Failures**
```bash
# Check if selectors are still valid
python cli.py product test <product_id>

# Try with Selenium for dynamic content
python cli.py product test <product_id> --selenium

# Check scraping logs
python cli.py monitor stats
```

**Email Notifications Not Working**
```bash
# Test email configuration
python cli.py config test-email

# Check environment variables
python cli.py config show
```

**Database Issues**
```bash
# Reinitialize database
python cli.py init

# Check database connection in logs
```

### Performance Issues

- **Slow scraping**: Reduce concurrent requests, increase delays
- **Memory usage**: Limit history retention, optimize queries
- **Database locks**: Use connection pooling, optimize transactions

## 📝 API Integration

The system provides JSON output for integration with other tools:

```bash
# Get monitoring stats as JSON
python cli.py monitor stats --format json

# Export price history
python cli.py report summary --format json --days 30
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Create an issue with detailed information
4. Include system configuration and error logs

## 🔮 Roadmap

### Planned Features
- **Web dashboard** with real-time monitoring
- **API endpoints** for external integrations
- **Machine learning** for price prediction
- **Advanced alerting** with Slack/Discord integration
- **Multi-currency support** with conversion rates
- **Proxy rotation** for enhanced reliability
- **Data export** to CSV/Excel formats
- **A/B testing** for scraping strategies

### Performance Improvements
- **Async scraping** for better concurrency
- **Caching layer** for frequently accessed data
- **Database optimization** with indexes and partitioning
- **Memory optimization** for large-scale monitoring

---

Built with ❤️ for e-commerce businesses looking to stay competitive through data-driven insights.