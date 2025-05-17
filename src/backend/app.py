import os
from flask import Flask, jsonify
from config.settings import DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor

# Import your service functions
from services.ticker_service import (
    fetch_ticker, fetch_news, compute_indicators, fetch_chart_data
)

app = Flask(__name__)

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
