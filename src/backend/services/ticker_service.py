import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import yfinance as yf

# load env
BASE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", ".."))
load_dotenv(os.path.join(ROOT, "env", "dev.env"))

DB_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def fetch_ticker(symbol):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT symbol, name, current_price, market_cap, sector, exchange
              FROM public.tickers
             WHERE symbol=%s
        """, (symbol,))
        return cur.fetchone()

def fetch_news(symbol, limit=10):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT title, url, published_at
              FROM public.news n
              JOIN public.tickers t ON t.id=n.ticker_id
             WHERE t.symbol=%s
             ORDER BY published_at DESC
             LIMIT %s
        """, (symbol, limit))
        return cur.fetchall()

def compute_indicators(symbol):
    # disable auto_adjust warning by specifying it
    df = yf.download(symbol, period="1mo", interval="1d", auto_adjust=False)["Close"]
    delta   = df.diff()
    up      = delta.clip(lower=0)
    down    = -delta.clip(upper=0)
    roll_up   = up.rolling(14).mean()
    roll_down = down.rolling(14).mean()
    rs       = roll_up / roll_down
    rsi      = 100.0 - (100.0 / (1.0 + rs))
    # drop NaNs, take last value, convert to native float
    latest = rsi.dropna().iloc[-1].item()
    return {"rsi": latest}



# src/backend/services/ticker_service.py

def fetch_chart_data(symbol, days=30):
    data = yf.download(symbol, period=f"{days}d", interval="1d")
    # ensure we pull each column as a Series, then to Python list
    return {
        "dates":   data.index.strftime("%Y-%m-%d").tolist(),
        "opens":   data["Open"].values.tolist(),
        "highs":   data["High"].values.tolist(),
        "lows":    data["Low"].values.tolist(),
        "closes":  data["Close"].values.tolist(),
        "volumes": data["Volume"].values.tolist(),
    }

