# src/backend/routes/watchlist_items.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from config.settings import DATABASE_URL
import psycopg2
import yfinance as yf
import os
from psycopg2.extras import RealDictCursor, Json

bp = Blueprint("items", __name__, url_prefix="/watchlists/<int:watchlist_id>/tickers")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@bp.route("", methods=["POST"])
@jwt_required()
def add_ticker(watchlist_id):
    user_id = get_jwt_identity()
    symbol  = request.json.get("symbol", "").upper().strip()
    if not symbol:
        return jsonify({"error":"`symbol` required"}), 400

    with get_conn() as conn, conn.cursor() as cur:
        # 0) ensure this watchlist belongs to the user
        cur.execute(
          "SELECT 1 FROM public.watchlists WHERE id=%s AND user_id=%s",
          (watchlist_id, user_id)
        )
        if not cur.fetchone():
            return jsonify({"error":"Not found"}), 404

        # 1) find or insert the ticker record
        cur.execute("SELECT id FROM public.tickers WHERE symbol=%s", (symbol,))
        row = cur.fetchone()
        if row:
            ticker_id = row["id"]
        else:
            # fetch metadata from yfinance
            info = yf.Ticker(symbol).info
            cur.execute("""
              INSERT INTO public.tickers
                (symbol, name, exchange, current_price, raw_info, created_at, updated_at)
              VALUES (%s,%s,%s,%s,%s, now(), now())
              RETURNING id
            """, [
              symbol,
              info.get("longName") or symbol,
              info.get("exchange") or None,
              info.get("regularMarketPrice") or None,
              Json(info),
            ])
            ticker_id = cur.fetchone()["id"]
            conn.commit()

        # 2) now link the ticker into the watchlist (avoid dupes)
        cur.execute("""
          INSERT INTO public.watchlist_items (watchlist_id, ticker_id)
          VALUES (%s,%s)
          ON CONFLICT (watchlist_id, ticker_id) DO NOTHING
        """, (watchlist_id, ticker_id))
        conn.commit()

    return ("", 204)


@bp.route("/<symbol>", methods=["DELETE"])
@jwt_required()
def remove_ticker(watchlist_id, symbol):
    user_id = get_jwt_identity()
    symbol  = symbol.upper().strip()

    with get_conn() as conn, conn.cursor() as cur:
        # delete only if that watchlist belongs to user
        cur.execute(
          """
          DELETE FROM public.watchlist_items wi
            USING public.watchlists w
           WHERE wi.watchlist_id=w.id
             AND wi.ticker_id=(SELECT id FROM public.tickers WHERE symbol=%s)
             AND w.id=%s AND w.user_id=%s
          """,
          (symbol, watchlist_id, user_id)
        )
        if cur.rowcount == 0:
            return jsonify({"error":"Not found"}), 404
        conn.commit()
        return "", 204

@bp.route("", methods=["GET"])
@jwt_required()
def list_tickers(watchlist_id):
    user_id = get_jwt_identity()
    with get_conn() as conn, conn.cursor() as cur:
        # ensure this watchlist belongs to the user
        cur.execute(
          "SELECT 1 FROM public.watchlists WHERE id=%s AND user_id=%s",
          (watchlist_id, user_id)
        )
        if not cur.fetchone():
            return jsonify({"error":"Not found"}), 404

        # fetch the symbols, names, and price
        cur.execute("""
          SELECT t.symbol, t.name, t.current_price
            FROM public.watchlist_items wi
            JOIN public.tickers t ON t.id=wi.ticker_id
           WHERE wi.watchlist_id=%s
        """, (watchlist_id,))
        return jsonify(cur.fetchall())
