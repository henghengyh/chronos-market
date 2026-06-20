import os
import pandas as pd
import yfinance as yf

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text

# ============================================
# Configuration
# ============================================

# Stock symbol to download
symbol = "NVDA"

# Historical data period
start_date = "2016-01-01"
end_date = "2026-06-15"

# Load variables from .env file
load_dotenv()

# PostgreSQL connection
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
db_url = (
    f"postgresql://{DB_USER}:"
    f"{DB_PASSWORD}@"
    f"{DB_HOST}:"
    f"{DB_PORT}/"
    f"{DB_NAME}"
)

def ingest_data(symbol="NVDA"):
    # ============================================
    # 1. EXTRACT: Download stock data
    # ============================================
    # Download historical market data from Yahoo Finance
    data = yf.download(
        symbol,
        start=start_date,
        end=end_date
    )

    # ============================================
    # 2. TRANSFORM: Prepare data for the database
    # ============================================
    data = data.reset_index()
    data.columns = data.columns.get_level_values(0) if hasattr(data.columns, 'get_level_values') else data.columns
    data.columns = [str(col) for col in data.columns]
    
    data = data[['Date', 'Close', 'Volume']]
    
    data = data.rename(columns={
        'Date': 'time',
        'Close': 'price_close',
        'Volume': 'volume'
    })
    data['symbol'] = symbol

    # ============================================
    # 3. LOAD: Store data in PostgreSQL
    # ============================================
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text(f"DELETE FROM market_data WHERE symbol = '{symbol}'"))
        conn.commit()
    data.to_sql(
        'market_data',
        engine,
        if_exists='append',
        index=False
    )
    print(f"Successfully ingested {len(data)} rows.")

if __name__ == "__main__":
    ingest_data(symbol)