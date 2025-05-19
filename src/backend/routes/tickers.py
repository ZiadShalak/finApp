# src/backend/routes/tickers.py
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta, timezone
import yfinance as yf
from config.settings import DATABASE_URL

bp = Blueprint("tickers", __name__, url_prefix="/tickers")

CACHE_TTL = timedelta(minutes=5)

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@bp.route("", methods=["GET"])
def list_tickers():
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
    with get_conn() as conn, conn.cursor() as cur:
        # read whatever's in the DB
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

        # single, UTC-aware staleness check
        now_utc = datetime.now(timezone.utc)
        last = row and row["last_fetched_at"]
        needs_refresh = (
            row is None
            or last is None
            # if last had no tzinfo, assume UTC
            or (last if last.tzinfo else last.replace(tzinfo=timezone.utc))
               < (now_utc - CACHE_TTL)
        )

        if needs_refresh:
            info = yf.Ticker(symbol).info
            # upsert every field you need
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
                  raw_info, updated_at, last_fetched_at
                ) VALUES (
                  %(symbol)s, %(longName)s, %(exchange)s, %(currency)s,
                  %(marketCap)s, %(sector)s, %(industry)s,
                  %(fullTimeEmployees)s, %(website)s, %(longBusinessSummary)s,
                  %(currentPrice)s, %(previousClose)s, %(openPrice)s,
                  %(dayHigh)s, %(dayLow)s, %(volume)s, %(averageVolume)s,
                  %(fiftyTwoWeekHigh)s, %(fiftyTwoWeekLow)s,
                  %(trailingPE)s, %(forwardPE)s, %(epsTrailingTwelveMonths)s,
                  %(priceToBook)s, %(beta)s, %(dividendRate)s, %(dividendYield)s,
                  %(raw_info)s, now(), now()
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
                "symbol":                   symbol,
                "longName":                 info.get("longName") or symbol,
                "exchange":                 info.get("exchange"),
                "currency":                 info.get("currency"),
                "marketCap":                info.get("marketCap"),
                "sector":                   info.get("sector"),
                "industry":                 info.get("industry"),
                "fullTimeEmployees":        info.get("fullTimeEmployees"),
                "website":                  info.get("website"),
                "longBusinessSummary":      info.get("longBusinessSummary"),
                "currentPrice":             info.get("regularMarketPrice"),
                "previousClose":            info.get("regularMarketPreviousClose"),
                "openPrice":                info.get("regularMarketOpen"),
                "dayHigh":                  info.get("dayHigh"),
                "dayLow":                   info.get("dayLow"),
                "volume":                   info.get("volume"),
                "averageVolume":            info.get("averageVolume"),
                "fiftyTwoWeekHigh":         info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow":          info.get("fiftyTwoWeekLow"),
                "trailingPE":               info.get("trailingPE"),
                "forwardPE":                info.get("forwardPE"),
                "epsTrailingTwelveMonths":  info.get("epsTrailingTwelveMonths"),
                "priceToBook":              info.get("priceToBook"),
                "beta":                     info.get("beta"),
                "dividendRate":             info.get("dividendRate"),
                "dividendYield":            info.get("dividendYield"),
                "raw_info":                 Json(info)
            })
            row = cur.fetchone()
            conn.commit()
        else:
            # if we didn’t refresh, just wrap the existing row as a dict
            row = dict(row)

        return row

@bp.route("/<symbol>/basic", methods=["GET"])
def ticker_basic(symbol):
    return jsonify(fetch_basic(symbol))

@bp.route("/<symbol>/news", methods=["GET"])
def ticker_news(symbol):
    news = yf.Ticker(symbol).news
    return jsonify(news[:20])

@bp.route("/<symbol>/indicators", methods=["GET"])
def ticker_indicators(symbol):
    # compute your RSI/MACD/etc here
    return jsonify({"rsi": 50, "macd": 0, "piotroski_score": 5})

@bp.route("/<symbol>/chart", methods=["GET"])
def ticker_chart(symbol):
    """Return OHLC+volume arrays for the last 30 days."""
    data = yf.download(symbol, period="1mo", interval="1d")

    # if yfinance returns no data, return empty lists
    if data.empty:
        return jsonify({
            "dates":   [],
            "opens":   [],
            "highs":   [],
            "lows":    [],
            "closes":  [],
            "volumes": []
        })

    # Now extract each column as a numpy array, then list
    return jsonify({
        "dates":   data.index.strftime("%Y-%m-%d").tolist(),
        "opens":   data["Open"].values.tolist(),
        "highs":   data["High"].values.tolist(),
        "lows":    data["Low"].values.tolist(),
        "closes":  data["Close"].values.tolist(),
        "volumes": data["Volume"].values.tolist(),
    })

