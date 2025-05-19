# src/backend/routes/tickers.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv
import yfinance as yf
from datetime import timedelta, datetime, timezone
from flask import Blueprint, jsonify, request
from config.settings import DATABASE_URL

bp = Blueprint("tickers", __name__, url_prefix="/tickers")

# Time‐to‐live for our cached rows
CACHE_TTL = timedelta(minutes=5)

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def fetch_basic(symbol):
    """Fetch the basic fields, refreshing from yfinance if stale."""
    with get_conn() as conn, conn.cursor() as cur:
        # 1) Try to read existing row
        cur.execute("""
            SELECT
              symbol, name, exchange, current_price,
              sector, market_cap, last_fetched_at
            FROM public.tickers
            WHERE symbol = %s
        """, (symbol,))
        row = cur.fetchone()

        # 2) We'll use a single timezone-aware now
        now_utc = datetime.now(timezone.utc)

        # 3) Determine if we need to refresh from yfinance
        needs_refresh = (
            row is None                              or
            row["last_fetched_at"] is None           or
            row["last_fetched_at"] < (now_utc - CACHE_TTL)
        )

        if needs_refresh:
            # 2) Fetch fresh data
            info = yf.Ticker(symbol).info

            # Upsert into the DB
            cur.execute("""
              INSERT INTO public.tickers
                (symbol, name, exchange, current_price,
                 sector, market_cap, raw_info,
                 created_at, updated_at, last_fetched_at)
              VALUES (%s,%s,%s,%s,%s,%s,%s, now(),now(),now())
              ON CONFLICT (symbol) DO UPDATE SET
                name            = EXCLUDED.name,
                exchange        = EXCLUDED.exchange,
                current_price   = EXCLUDED.current_price,
                sector          = EXCLUDED.sector,
                market_cap      = EXCLUDED.market_cap,
                raw_info        = EXCLUDED.raw_info,
                updated_at      = now(),
                last_fetched_at = now()
              RETURNING
                symbol, name, exchange, current_price,
                sector, market_cap
            """, [
              symbol,
              info.get("longName")         or symbol,
              info.get("exchange")         or None,
              info.get("regularMarketPrice") or None,
              info.get("sector")           or None,
              info.get("marketCap")        or None,
              Json(info)
            ])
            row = cur.fetchone()
            conn.commit()

        return dict(row)

@bp.route("", methods=["GET"])
def list_tickers():
    """Autocomplete / small search against master_tickers table."""
    q = (request.args.get("search","") + "%").upper()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT symbol,name
            FROM public.master_tickers
           WHERE symbol ILIKE %s OR name ILIKE %s
           ORDER BY symbol
           LIMIT 10
        """, (q,q))
        return jsonify(cur.fetchall())

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

def fetch_news(symbol, limit=20):
    """Fetch news for a ticker using yfinance."""
    ticker = yf.Ticker(symbol)
    news = ticker.news[:limit]
    return news

def compute_indicators(symbol):
    """Compute technical indicators for a ticker."""
    ticker = yf.Ticker(symbol)
    # TODO: Implement technical indicators
    return {
        "rsi": None,
        "macd": None,
        "piotroski_score": None
    }


@bp.route("/<symbol>/basic")
def ticker_basic(symbol):
    return jsonify(fetch_basic(symbol))

@bp.route("/<symbol>/news")
def ticker_news(symbol):
    return jsonify(fetch_news(symbol, limit=20))

@bp.route("/<symbol>/indicators")
def ticker_indicators(symbol):
    return jsonify(compute_indicators(symbol))

@bp.route("/<symbol>/chart")
def ticker_chart(symbol):
    return jsonify(fetch_chart_data(symbol, days=30))
