# src/backend/routes/watchlist_items.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from config.settings import DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor

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
        # verify ownership
        cur.execute(
          "SELECT 1 FROM public.watchlists WHERE id=%s AND user_id=%s",
          (watchlist_id, user_id)
        )
        if not cur.fetchone():
            return jsonify({"error":"Watchlist not found"}), 404

        # get ticker id
        cur.execute(
          "SELECT id FROM public.tickers WHERE symbol=%s",
          (symbol,)
        )
        t = cur.fetchone()
        if not t:
            return jsonify({"error":"Ticker not found"}), 404

        # insert relationship
        cur.execute(
          "INSERT INTO public.watchlist_items (watchlist_id,ticker_id) "
          "VALUES (%s,%s) ON CONFLICT DO NOTHING",
          (watchlist_id, t["id"])
        )
        conn.commit()
        return "", 204

@bp.route("/<symbol>", methods=["DELETE"])
@jwt_required()
def remove_ticker(watchlist_id, symbol):
    user_id = get_jwt_identity()
    symbol  = symbol.upper().strip()

    with get_conn() as conn, conn.cursor() as cur:
        # ensure ownership
        cur.execute(
          "DELETE FROM public.watchlist_items wi USING public.watchlists w "
          "WHERE wi.watchlist_id=w.id AND wi.ticker_id=("
            "SELECT id FROM public.tickers WHERE symbol=%s"
          ") AND w.id=%s AND w.user_id=%s",
          (symbol, watchlist_id, user_id)
        )
        if cur.rowcount == 0:
            return jsonify({"error":"Not found"}), 404
        conn.commit()
        return "", 204
