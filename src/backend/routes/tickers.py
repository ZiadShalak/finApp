import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import yfinance as yf
from config.settings import DATABASE_URL

bp = Blueprint("tickers", __name__, url_prefix="/tickers")

CACHE_TTL = timedelta(minutes=5)

def get_conn():
    """New DB connection returning dict-rows."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@bp.route("", methods=["GET"])
def list_tickers():
    """
    Autocomplete search against master_tickers.
    Returns up to 10 { symbol, name } rows.
    """
    q = (request.args.get("search","") + "%").upper()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT symbol, name
            FROM public.master_tickers
           WHERE symbol ILIKE %s OR name ILIKE %s
           ORDER BY symbol
           LIMIT 10
        """, (q,q))
        return jsonify(cur.fetchall())


def fetch_basic(symbol):
    """
    Fetch full metadata from `public.tickers`, refreshing from yfinance if
    our cache is older than CACHE_TTL or missing.
    """
    with get_conn() as conn, conn.cursor() as cur:
        # 1) check our local row
        cur.execute("""
            SELECT
              symbol, name, exchange, currency,
              market_cap, sector, industry,
              full_time_employees, website, long_business_summary,
              current_price, previous_close, open_price,
              day_high, day_low, volume, avg_volume,
              fifty_two_week_high, fifty_two_week_low,
              trailing_pe, forward_pe, eps_ttm,
              price_to_book, beta, dividend_rate, dividend_yield,
              last_fetched_at
            FROM public.tickers
            WHERE symbol = %s
        """, (symbol,))
        row = cur.fetchone()

        # 2) decide if we need to refresh
        needs = (
            row is None or
            row["last_fetched_at"] is None or
            row["last_fetched_at"] < datetime.utcnow() - CACHE_TTL
        )

        if needs:
            info = yf.Ticker(symbol).info
            cur.execute("""
                INSERT INTO public.tickers (
                  symbol, name, exchange, currency,
                  market_cap, sector, industry,
                  full_time_employees, website, long_business_summary,
                  current_price, previous_close, open_price,
                  day_high, day_low, volume, avg_volume,
                  fifty_two_week_high, fifty_two_week_low,
                  trailing_pe, forward_pe, eps_ttm,
                  price_to_book, beta, dividend_rate, dividend_yield,
                  raw_info,
                  updated_at, last_fetched_at
                )
                VALUES (
                  %(symbol)s, %(longName)s, %(exchange)s, %(currency)s,
                  %(marketCap)s, %(sector)s, %(industry)s,
                  %(fullTimeEmployees)s, %(website)s, %(longBusinessSummary)s,
                  %(currentPrice)s, %(previousClose)s, %(openPrice)s,
                  %(dayHigh)s, %(dayLow)s, %(volume)s, %(averageVolume)s,
                  %(fiftyTwoWeekHigh)s, %(fiftyTwoWeekLow)s,
                  %(trailingPE)s, %(forwardPE)s, %(epsTrailingTwelveMonths)s,
                  %(priceToBook)s, %(beta)s, %(dividendRate)s, %(dividendYield)s,
                  %(raw_info)s,
                  now(), now()
                )
                ON CONFLICT (symbol) DO UPDATE SET
                  name                  = EXCLUDED.name,
                  exchange              = EXCLUDED.exchange,
                  currency              = EXCLUDED.currency,
                  market_cap            = EXCLUDED.market_cap,
                  sector                = EXCLUDED.sector,
                  industry              = EXCLUDED.industry,
                  full_time_employees   = EXCLUDED.full_time_employees,
                  website               = EXCLUDED.website,
                  long_business_summary = EXCLUDED.long_business_summary,
                  current_price         = EXCLUDED.current_price,
                  previous_close        = EXCLUDED.previous_close,
                  open_price            = EXCLUDED.open_price,
                  day_high              = EXCLUDED.day_high,
                  day_low               = EXCLUDED.day_low,
                  volume                = EXCLUDED.volume,
                  avg_volume            = EXCLUDED.avg_volume,
                  fifty_two_week_high   = EXCLUDED.fifty_two_week_high,
                  fifty_two_week_low    = EXCLUDED.fifty_two_week_low,
                  trailing_pe           = EXCLUDED.trailing_pe,
                  forward_pe            = EXCLUDED.forward_pe,
                  eps_ttm               = EXCLUDED.eps_ttm,
                  price_to_book         = EXCLUDED.price_to_book,
                  beta                  = EXCLUDED.beta,
                  dividend_rate         = EXCLUDED.dividend_rate,
                  dividend_yield        = EXCLUDED.dividend_yield,
                  raw_info              = EXCLUDED.raw_info,
                  updated_at            = now(),
                  last_fetched_at       = now()
                RETURNING
                  symbol, name, exchange, currency,
                  market_cap, sector, industry,
                  full_time_employees, website, long_business_summary,
                  current_price, previous_close, open_price,
                  day_high, day_low, volume, avg_volume,
                  fifty_two_week_high, fifty_two_week_low,
                  trailing_pe, forward_pe, eps_ttm,
                  price_to_book, beta, dividend_rate, dividend_yield
            """, {
                "symbol":                     symbol,
                "longName":                   info.get("longName") or symbol,
                "exchange":                   info.get("exchange"),
                "currency":                   info.get("currency"),
                "marketCap":                  info.get("marketCap"),
                "sector":                     info.get("sector"),
                "industry":                   info.get("industry"),
                "fullTimeEmployees":          info.get("fullTimeEmployees"),
                "website":                    info.get("website"),
                "longBusinessSummary":        info.get("longBusinessSummary"),
                "currentPrice":               info.get("regularMarketPrice"),
                "previousClose":              info.get("regularMarketPreviousClose"),
                "openPrice":                  info.get("regularMarketOpen"),
                "dayHigh":                    info.get("dayHigh"),
                "dayLow":                     info.get("dayLow"),
                "volume":                     info.get("volume"),
                "averageVolume":              info.get("averageVolume"),
                "fiftyTwoWeekHigh":           info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow":            info.get("fiftyTwoWeekLow"),
                "trailingPE":                 info.get("trailingPE"),
                "forwardPE":                  info.get("forwardPE"),
                "epsTrailingTwelveMonths":    info.get("epsTrailingTwelveMonths"),
                "priceToBook":                info.get("priceToBook"),
                "beta":                       info.get("beta"),
                "dividendRate":               info.get("dividendRate"),
                "dividendYield":              info.get("dividendYield"),
                "raw_info":                   Json(info)
            })
            row = cur.fetchone()
            conn.commit()
        else:
            row = dict(row)

        return row

@bp.route("/<symbol>/basic", methods=["GET"])
def ticker_basic(symbol):
    """Return the up-to-date metadata fields for symbol."""
    return jsonify(fetch_basic(symbol))

# (you can leave your /<symbol>/news, /indicators, /chart as-is)
