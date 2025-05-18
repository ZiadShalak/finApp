from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from config.settings import DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor

bp = Blueprint("tickers", __name__, url_prefix="/tickers")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# routes/tickers.py
@bp.route("", methods=["GET"])
def list_tickers():
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
