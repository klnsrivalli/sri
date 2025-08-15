#!/usr/bin/env python3
"""
Quick Start Script for E-commerce Competitor Monitoring Agent
Automates the initial setup process
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_environment():
    """Set up the environment file."""
    print("🔄 Setting up environment file...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    
    if env_file.exists():
        print("⚠️  .env file already exists, skipping creation")
        return True
    
    try:
        shutil.copy(env_example, env_file)
        print("✅ Environment file created")
        print("📝 Please edit .env file with your configuration")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def install_dependencies():
    """Install Python dependencies."""
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def initialize_database():
    """Initialize the database."""
    return run_command("python scripts/init_db.py", "Initializing database")

def add_sample_products():
    """Add sample products."""
    return run_command("python scripts/add_sample_products.py", "Adding sample products")

def run_tests():
    """Run the test suite."""
    return run_command("python test_setup.py", "Running tests")

def main():
    """Main setup function."""
    print("🚀 E-commerce Competitor Monitoring Agent - Quick Start")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("❌ Database initialization failed")
        sys.exit(1)
    
    # Add sample products
    if not add_sample_products():
        print("⚠️  Sample products could not be added (this is optional)")
    
    # Run tests
    if not run_tests():
        print("❌ Tests failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start the monitoring agent: python main.py")
    print("3. Start the dashboard: python dashboard.py")
    print("4. Open http://localhost:8000/docs for API documentation")
    print("5. Open http://localhost:8050 for the web dashboard")
    
    print("\n💡 Tips:")
    print("- Use SQLite for development (already configured)")
    print("- Configure email/Telegram alerts in .env for notifications")
    print("- Adjust monitoring interval in .env based on your needs")
    print("- Check logs in competitor_monitor.log for debugging")

if __name__ == "__main__":
    main()