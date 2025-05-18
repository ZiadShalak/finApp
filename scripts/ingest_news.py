#!/usr/bin/env python3
import os
import requests
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv


# 1) Compute path to env/dev.env, relative to this script
here = os.path.dirname(__file__)
dotenv_path = os.path.join(here, "../env/dev.env")

# 2) Load it explicitly
load_dotenv(dotenv_path)
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY not set in env/dev.env")

# # Load environment variables
api_key = os.getenv("API_KEY")
db_url  = os.getenv("DATABASE_URL")

# if not api_key:
#     raise RuntimeError("API_KEY not set in env/dev.env")

# Connect to the database
conn = psycopg2.connect(db_url)
cur  = conn.cursor()

# For each ticker symbol
cur.execute("SELECT id, symbol FROM public.tickers")
for ticker_id, symbol in cur.fetchall():
    print(f"Fetching news for {symbol}...")
    params = {
        "apiKey": api_key,
        "q": symbol,
        "pageSize": 20,
        "language": "en",
    }
    r = requests.get("https://newsapi.org/v2/everything", params=params)
    data = r.json().get("articles", [])
    for art in data:
        # use URL+publishedAt as a unique key, or generate a hash
        article_uid = hash(art['url'] + art['publishedAt'])
        cur.execute("""
            INSERT INTO public.news
              (article_id, ticker_id, title, url,
               description, published_at, crawl_date,
               source, tickers, tags, raw_json)
            VALUES (%s, %s, %s, %s, %s, %s, now(),
                    %s, %s, %s, %s)
            ON CONFLICT (article_id) DO UPDATE SET
              title       = EXCLUDED.title,
              description = EXCLUDED.description,
              updated_at  = now(),
              raw_json    = EXCLUDED.raw_json;
        """, [
            article_uid,
            ticker_id,
            art.get("title"),
            art.get("url"),
            art.get("description"),
            art.get("publishedAt"),
            art.get("source",{}).get("name"),
            [symbol],    # tickers array
            [],          # no tags field
            Json(art),
        ])
    conn.commit()
    print(f"  {len(data)} articles upserted.")

cur.close()
conn.close()
print("Done.")
