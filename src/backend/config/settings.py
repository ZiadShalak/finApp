# src/backend/config/settings.py
import os, pathlib
from dotenv import load_dotenv

BASE = pathlib.Path(__file__).parents[3]   # project-root/src/backend
load_dotenv(BASE / "env" / "dev.env")

DATABASE_URL  = os.getenv("DATABASE_URL")
API_KEY = os.getenv("API_KEY")
NEWSAPI_KEY    = os.getenv("NEWSAPI_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
