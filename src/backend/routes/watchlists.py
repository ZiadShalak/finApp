# src/backend/routes/watchlists.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from config.settings import DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor

bp = Blueprint("watchlists", __name__, url_prefix="/watchlists")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@bp.route("", methods=["GET"])
@jwt_required()
def list_watchlists():
    user_id = get_jwt_identity()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
          "SELECT id, name, created_at FROM public.watchlists WHERE user_id=%s",
          (user_id,)
        )
        return jsonify(cur.fetchall())

@bp.route("", methods=["POST"])
@jwt_required()
def create_watchlist():
    user_id = get_jwt_identity()
    name    = request.json.get("name", "").strip()
    if not name:
        return jsonify({"error":"`name` required"}), 400

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
          "INSERT INTO public.watchlists (user_id,name) VALUES (%s,%s) "
          "RETURNING id,name,created_at",
          (user_id, name)
        )
        wl = cur.fetchone()
        conn.commit()
        return jsonify(wl), 201

@bp.route("/<int:watchlist_id>", methods=["PUT"])
@jwt_required()
def update_watchlist(watchlist_id):
    user_id = get_jwt_identity()
    name    = request.json.get("name", "").strip()
    if not name:
        return jsonify({"error":"`name` required"}), 400

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
          "UPDATE public.watchlists SET name=%s "
          "WHERE id=%s AND user_id=%s RETURNING id,name,created_at",
          (name, watchlist_id, user_id)
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error":"Not found"}), 404
        conn.commit()
        return jsonify(row)

@bp.route("/<int:watchlist_id>", methods=["DELETE"])
@jwt_required()
def delete_watchlist(watchlist_id):
    user_id = get_jwt_identity()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
          "DELETE FROM public.watchlists WHERE id=%s AND user_id=%s",
          (watchlist_id, user_id)
        )
        if cur.rowcount == 0:
            return jsonify({"error":"Not found"}), 404
        conn.commit()
        return "", 204
