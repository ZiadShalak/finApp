# scripts/ingest_master.py

import csv
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import os

# 1) load env/dev.env
here = os.path.dirname(__file__)
load_dotenv(os.path.join(here, "../env/dev.env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in env/dev.env")

print("🔗 Connecting to:", DATABASE_URL)

# 2) point at your uploaded CSV
csv_path = os.path.join(here, "flat-ui__data-Mon May 19 2025.csv")
print("📄 Looking for CSV at:", csv_path)
print("🗂️  Exists?", os.path.exists(csv_path))

# 3) Run the upsert
conn = psycopg2.connect(DATABASE_URL)
with conn, conn.cursor() as cur, open(csv_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    print("CSV columns:", reader.fieldnames)

    for i, row in enumerate(reader, start=1):
        symbol = row["Symbol"].strip().upper()
        name   = row["Security Name"].strip()
        # default exchange
        exchange = "NASDAQ"

        print(f"Ingesting row {i}: {symbol} – {name}")

        cur.execute("""
          INSERT INTO public.master_tickers(symbol, name, exchange, last_updated)
          VALUES (%s,%s,%s,%s)
          ON CONFLICT(symbol) DO UPDATE SET
            name         = EXCLUDED.name,
            exchange     = EXCLUDED.exchange,
            last_updated = EXCLUDED.last_updated
        """, (symbol, name, exchange, datetime.utcnow()))

    # 4) verify count
    cur.execute("SELECT COUNT(*) FROM public.master_tickers")
    total = cur.fetchone()[0]
    print("✅ master_tickers now has", total, "rows")

    conn.commit()
