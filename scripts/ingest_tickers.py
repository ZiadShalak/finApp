#!/usr/bin/env python3
import os
import yfinance as yf
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

# 1. Load env
load_dotenv("env/dev.env")
db_url = os.getenv("DATABASE_URL")

# 2. Connect
conn = psycopg2.connect(db_url)
cur = conn.cursor()

# 3. List of symbols to seed (extend as needed)
symbols = ["AAPL", "MSFT", "GOOGL"]

for sym in symbols:
    info = yf.Ticker(sym).info
    # 4. Upsert into tickers
    cur.execute("""
        INSERT INTO public.tickers 
          (symbol, name, exchange, currency, market_cap, sector, industry,
           full_time_employees, website, long_business_summary, current_price, previous_close, open_price, day_high, day_low,
           volume, avg_volume, fifty_two_week_high, fifty_two_week_low,
           trailing_pe, forward_pe, eps_ttm, price_to_book, beta,
           dividend_rate, dividend_yield, raw_info)
        VALUES (%s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s)
        ON CONFLICT (symbol) DO UPDATE SET
          name = EXCLUDED.name,
          exchange = EXCLUDED.exchange,
          currency = EXCLUDED.currency,
          market_cap = EXCLUDED.market_cap,
          sector = EXCLUDED.sector,
          industry = EXCLUDED.industry,
          full_time_employees = EXCLUDED.full_time_employees,
          website = EXCLUDED.website,
          long_business_summary = EXCLUDED.long_business_summary,
          current_price = EXCLUDED.current_price,
          previous_close = EXCLUDED.previous_close,
          open_price = EXCLUDED.open_price,
          day_high = EXCLUDED.day_high,
          day_low = EXCLUDED.day_low,
          volume = EXCLUDED.volume,
          avg_volume = EXCLUDED.avg_volume,
          fifty_two_week_high = EXCLUDED.fifty_two_week_high,
          fifty_two_week_low = EXCLUDED.fifty_two_week_low,
          trailing_pe = EXCLUDED.trailing_pe,
          forward_pe = EXCLUDED.forward_pe,
          eps_ttm = EXCLUDED.eps_ttm,
          price_to_book = EXCLUDED.price_to_book,
          beta = EXCLUDED.beta,
          dividend_rate = EXCLUDED.dividend_rate,
          dividend_yield = EXCLUDED.dividend_yield,
          raw_info = EXCLUDED.raw_info,
          updated_at = now();
    """, [
        sym,
        info.get("longName"),
        info.get("exchange"),
        info.get("currency"),
        info.get("marketCap"),
        info.get("sector"),
        info.get("industry"),
        info.get("fullTimeEmployees"),
        info.get("website"),
        info.get("longBusinessSummary"),
        info.get("regularMarketPrice"),
        info.get("previousClose"),
        info.get("open"),
        info.get("dayHigh"),
        info.get("dayLow"),
        info.get("volume"),
        info.get("averageVolume"),
        info.get("fiftyTwoWeekHigh"),
        info.get("fiftyTwoWeekLow"),
        info.get("trailingPE"),
        info.get("forwardPE"),
        info.get("trailingEps"),
        info.get("priceToBook"),
        info.get("beta"),
        info.get("dividendRate"),
        info.get("dividendYield"),
        Json(info),
    ])
    conn.commit()
    print(f"{sym} upserted.")

cur.close()
conn.close()
