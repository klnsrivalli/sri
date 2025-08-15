# E-commerce Competitor Monitoring Agent - Setup Guide

This guide will help you set up and run the e-commerce competitor monitoring agent.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Chrome browser (for Selenium web scraping)
- Git (optional, for version control)

## Installation

### 1. Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd e-commerce-competitor-monitor

# Or download and extract the project files
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
nano .env  # or use your preferred text editor
```

### 4. Configure Environment Variables

Edit the `.env` file with your settings:

```env
# Database Configuration
DATABASE_URL=sqlite:///./competitor_monitor.db  # Use SQLite for development

# For production, use PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/competitor_monitor

# Telegram Bot Configuration (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here

# Monitoring Configuration
MONITORING_INTERVAL=3600  # seconds (1 hour)
MAX_RETRIES=3
REQUEST_DELAY=2  # seconds between requests
```

### 5. Initialize the Database

```bash
python scripts/init_db.py
```

This will:
- Create all necessary database tables
- Add sample competitors (Amazon, eBay, Walmart)
- Set up the basic database structure

### 6. Add Sample Products (Optional)

```bash
python scripts/add_sample_products.py
```

This adds sample Amazon products for testing.

## Running the Application

### 1. Start the Monitoring Agent

```bash
python main.py
```

This starts the FastAPI server with the monitoring agent. The API will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 2. Start the Dashboard (Optional)

In a new terminal:

```bash
python dashboard.py
```

The dashboard will be available at: http://localhost:8050

## Usage

### Adding Products to Monitor

#### Via API

```bash
curl -X POST "http://localhost:8000/api/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 15 Pro",
    "url": "https://amazon.com/iphone-15-pro",
    "competitor": "Amazon",
    "category": "Electronics",
    "target_price": 999.99
  }'
```

#### Via Dashboard

1. Open http://localhost:8050 in your browser
2. Use the dashboard interface to add products
3. View monitoring status and price history

### API Endpoints

- `GET /api/status` - Get monitoring status
- `GET /api/products` - List all monitored products
- `POST /api/products` - Add new product to monitor
- `GET /api/products/{id}/history` - Get price history for a product
- `GET /api/competitors` - Get competitor summary
- `POST /api/monitor/start` - Start monitoring
- `POST /api/monitor/stop` - Stop monitoring
- `POST /api/monitor/run-cycle` - Run a single monitoring cycle

### Setting Up Alerts

The system automatically sets up default alerts for new products:
- Price drop alerts (5% threshold by default)
- Stock change alerts

You can configure alerts via the API or modify the default settings in the code.

## Configuration Options

### Monitoring Settings

- `MONITORING_INTERVAL`: How often to check prices (in seconds)
- `MAX_RETRIES`: Number of retry attempts for failed requests
- `REQUEST_DELAY`: Delay between requests to avoid rate limiting

### Scraping Settings

- `HEADLESS_BROWSER`: Run browser in headless mode (recommended)
- `USER_AGENT_ROTATION`: Rotate user agents to avoid detection
- `PROXY_ENABLED`: Use proxy for requests (optional)

### Alert Settings

- `PRICE_CHANGE_THRESHOLD`: Minimum price change percentage to trigger alerts
- `STOCK_ALERT_ENABLED`: Enable stock change alerts
- `PROMOTION_ALERT_ENABLED`: Enable promotion alerts

## Testing

Run the test script to verify your setup:

```bash
python test_setup.py
```

This will test:
- All imports work correctly
- Database operations
- Scraper functionality

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Errors**: Check your database URL in `.env`
   ```bash
   # For SQLite (default)
   DATABASE_URL=sqlite:///./competitor_monitor.db
   ```

3. **Chrome Driver Issues**: The system automatically downloads ChromeDriver
   - Make sure Chrome is installed
   - Check internet connection for driver download

4. **Rate Limiting**: Increase `REQUEST_DELAY` in `.env`
   ```env
   REQUEST_DELAY=5  # 5 seconds between requests
   ```

### Logs

Check the log file for detailed information:
```bash
tail -f competitor_monitor.log
```

## Production Deployment

### Database

For production, use PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/competitor_monitor
```

### Process Management

Use a process manager like systemd or supervisor:

```ini
[program:competitor-monitor]
command=python /path/to/main.py
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/competitor-monitor.err.log
stdout_logfile=/var/log/competitor-monitor.out.log
```

### Security

1. Use environment variables for sensitive data
2. Set up proper firewall rules
3. Use HTTPS in production
4. Implement authentication for the API

## Support

For issues and questions:
1. Check the logs: `competitor_monitor.log`
2. Run the test script: `python test_setup.py`
3. Review the configuration in `.env`
4. Check the API documentation at http://localhost:8000/docs

## License

This project is licensed under the MIT License.