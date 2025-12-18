"""Configuration module for KouranBot."""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Fix for Coolify/Heroku: postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Bot Configuration
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "15"))
JSON_URL = os.getenv(
    "JSON_URL",
    "https://raw.githubusercontent.com/MrSunshyne/mauritius-dataset-electricity/main/data/power-outages.latest.json"
)

# Pagination Configuration
LOCALITIES_PER_PAGE = 10
DISTRICTS_PER_ROW = 2

# Rate Limiting
TELEGRAM_RATE_LIMIT = 30  # messages per second
