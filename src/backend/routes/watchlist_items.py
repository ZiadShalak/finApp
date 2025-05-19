from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from config.settings import DATABASE_URL
import psycopg2
import yfinance as yf
from psycopg2.extras import RealDictCursor, Json

# Blueprint at /watchlists/<watchlist_id>/tickers
bp = Blueprint(
    "items", __name__,
    url_prefix="/watchlists/<int:watchlist_id>/tickers"
)

def get_conn():
    """Return a new psycopg2 connection that yields dict rows."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@bp.route("", methods=["POST"])
@jwt_required()
def add_ticker(watchlist_id):
    """Add (or refresh) a ticker in the DB, then link it to the watchlist."""
    user_id = get_jwt_identity()
    symbol  = (request.json.get("symbol") or "").upper().strip()
    if not symbol:
        return jsonify({"error": "`symbol` required"}), 400

    with get_conn() as conn, conn.cursor() as cur:
        # 0) ensure this watchlist belongs to the current user
        cur.execute(
            "SELECT 1 FROM public.watchlists WHERE id=%s AND user_id=%s",
            (watchlist_id, user_id))
        if not cur.fetchone():
            return jsonify({"error": "watchlist not found"}), 404

        # 1) upsert the ticker metadata in public.tickers
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
                created_at, updated_at, last_fetched_at
            ) VALUES (
                %(symbol)s, %(longName)s, %(exchange)s, %(currency)s,
                %(marketCap)s, %(sector)s, %(industry)s,
                %(fullTimeEmployees)s, %(website)s, %(longBusinessSummary)s,
                %(currentPrice)s, %(previousClose)s, %(openPrice)s,
                %(dayHigh)s, %(dayLow)s, %(volume)s, %(averageVolume)s,
                %(fiftyTwoWeekHigh)s, %(fiftyTwoWeekLow)s,
                %(trailingPE)s, %(forwardPE)s, %(epsTrailingTwelveMonths)s,
                %(priceToBook)s, %(beta)s, %(dividendRate)s, %(dividendYield)s,
                %(raw_info)s,
                now(), now(), now()
            )
            ON CONFLICT (symbol) DO UPDATE SET
                name                   = EXCLUDED.name,
                exchange               = EXCLUDED.exchange,
                currency               = EXCLUDED.currency,
                market_cap             = EXCLUDED.market_cap,
                sector                 = EXCLUDED.sector,
                industry               = EXCLUDED.industry,
                full_time_employees    = EXCLUDED.full_time_employees,
                website                = EXCLUDED.website,
                long_business_summary  = EXCLUDED.long_business_summary,
                current_price          = EXCLUDED.current_price,
                previous_close         = EXCLUDED.previous_close,
                open_price             = EXCLUDED.open_price,
                day_high               = EXCLUDED.day_high,
                day_low                = EXCLUDED.day_low,
                volume                 = EXCLUDED.volume,
                avg_volume             = EXCLUDED.avg_volume,
                fifty_two_week_high    = EXCLUDED.fifty_two_week_high,
                fifty_two_week_low     = EXCLUDED.fifty_two_week_low,
                trailing_pe            = EXCLUDED.trailing_pe,
                forward_pe             = EXCLUDED.forward_pe,
                eps_ttm                = EXCLUDED.eps_ttm,
                price_to_book          = EXCLUDED.price_to_book,
                beta                   = EXCLUDED.beta,
                dividend_rate          = EXCLUDED.dividend_rate,
                dividend_yield         = EXCLUDED.dividend_yield,
                raw_info               = EXCLUDED.raw_info,
                updated_at             = now(),
                last_fetched_at        = now()
            RETURNING id
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
        ticker_id = cur.fetchone()["id"]
        conn.commit()

        # 2) link ticker → watchlist (skip if already linked)
        cur.execute("""
            INSERT INTO public.watchlist_items (watchlist_id, ticker_id)
            VALUES (%s, %s)
            ON CONFLICT (watchlist_id, ticker_id) DO NOTHING
        """, (watchlist_id, ticker_id))
        conn.commit()

    return ("", 204)


@bp.route("/<symbol>", methods=["DELETE"])
@jwt_required()
def remove_ticker(watchlist_id, symbol):
    """Remove the given symbol from this watchlist (if owned)."""
    user_id = get_jwt_identity()
    symbol  = symbol.upper().strip()

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            DELETE FROM public.watchlist_items wi
              USING public.watchlists w
             WHERE wi.watchlist_id = w.id
               AND w.user_id      = %s
               AND w.id           = %s
               AND wi.ticker_id   = (
                   SELECT id FROM public.tickers WHERE symbol = %s
               )
        """, (user_id, watchlist_id, symbol))

        if cur.rowcount == 0:
            return jsonify({"error": "Not found"}), 404

        conn.commit()
        return ("", 204)


@bp.route("", methods=["GET"])
@jwt_required()
def list_tickers(watchlist_id):
    """Return all symbols, names & current_price for this watchlist."""
    user_id = get_jwt_identity()
    with get_conn() as conn, conn.cursor() as cur:
        # ensure ownership
        cur.execute(
            "SELECT 1 FROM public.watchlists WHERE id=%s AND user_id=%s",
            (watchlist_id, user_id))
        if not cur.fetchone():
            return jsonify({"error":"Not found"}), 404

        cur.execute("""
            SELECT t.symbol, t.name, t.current_price
              FROM public.watchlist_items wi
              JOIN public.tickers t ON t.id = wi.ticker_id
             WHERE wi.watchlist_id = %s
        """, (watchlist_id,))
        return jsonify(cur.fetchall())
