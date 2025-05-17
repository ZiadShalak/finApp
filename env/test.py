import os, psycopg2
from dotenv import load_dotenv

load_dotenv("env/dev.env")
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
print("Connected to:", conn.get_dsn_parameters()['dbname'])
conn.close()