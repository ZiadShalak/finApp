# src/backend/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from passlib.hash import bcrypt
from config.settings import DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt","pbkdf2_sha256"], deprecated="auto")
bp = Blueprint("auth", __name__, url_prefix="/auth")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"error":"email and password required"}), 400

    pw_hash = pwd_ctx.hash(password)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM public.users WHERE email=%s", (email,))
        if cur.fetchone():
            return jsonify({"error":"email already registered"}), 409
        cur.execute(
            "INSERT INTO public.users (email,password_hash) VALUES (%s,%s) RETURNING id",
            (email, pw_hash)
        )
        user_id = cur.fetchone()["id"]
        conn.commit()
    return jsonify({"msg":"user created","user_id":user_id}), 201

@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"error":"email and password required"}), 400

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id,password_hash FROM public.users WHERE email=%s", (email,))
        user = cur.fetchone()
        if not pwd_ctx.verify(password, user["password_hash"]):
            return jsonify({"error":"invalid credentials"}), 401

    token = create_access_token(identity=user["id"])
    return jsonify({"access_token": token}), 200
