import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config.settings import DATABASE_URL, JWT_SECRET_KEY
import pprint
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

# allow all origins for all routes (moved after JWT config)
CORS(app)

# Import your service functions
from services.ticker_service import (
    fetch_ticker, fetch_news, compute_indicators, fetch_chart_data
)

# DB
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# register blueprints (you'll create these next)
from routes.watchlists import bp as watchlists_bp
from routes.watchlist_items import bp as items_bp
from routes.auth import bp as auth_bp
from routes.tickers import bp as tickers_bp


app.register_blueprint(watchlists_bp)
app.register_blueprint(items_bp)
app.register_blueprint(tickers_bp)
app.register_blueprint(auth_bp)

# <<< Add this block right here >>>
print("Registered endpoints:")
for rule in app.url_map.iter_rules():
    pprint.pprint(f"{rule.methods} -> {rule.rule}")
print("---------------------")

# Single-detail endpoint
@app.route("/tickers/<symbol>")
def ticker_detail(symbol):
    t = fetch_ticker(symbol)
    if not t:
        return jsonify({"error":"Ticker not found"}), 404

    return jsonify({
        **t,
        "news":       fetch_news(symbol, limit=20),
        "indicators": compute_indicators(symbol),
        "chart_data": fetch_chart_data(symbol, days=30)
    })

if __name__ == "__main__":
    app.run(debug=True)
