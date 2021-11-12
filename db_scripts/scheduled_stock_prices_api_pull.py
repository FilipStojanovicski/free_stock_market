import pandas as pd
from postgres_functions import insert_row_query
import psycopg2
import pandas.io.sql as psql
from datetime import datetime, timezone, timedelta
from alpaca_trade_api.rest import REST, TimeFrame
import logging
import os
from config import (DEBUG, pg_user_dev, pg_pass_dev, pg_host_dev, pg_port_dev, pg_db_dev, pg_user_prod,
pg_pass_prod, pg_host_prod, pg_port_prod, pg_db_prod, APCA_API_KEY_ID, APCA_API_SECRET_KEY)
import time

current_time = datetime.now(timezone.utc)

# Create a logger
#LOG_NAME = str(current_time.timestamp()).split('.')[0]
LOG_NAME = "latest_job"
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
handler = logging.FileHandler("logs/" + LOG_NAME + '.log', 'w', 'utf-8')
handler.setFormatter(logging.Formatter('%(name)s %(message)s'))
handler.setLevel("DEBUG")
root_logger.addHandler(handler)

# Define the schema for the stock prices table
stock_prices_schema = {
    "primary_key": "id",
    "schema": "stock_trading_marketplace",
    "table_name": "stock_prices",
    "fields": {
        "id": {
            "nullable": False,
            "unique": True,
            "postgres_type": "INTEGER",
            "type": "int64"},
        "symbol": {
            "nullable": False,
            "unique": False,
            "postgres_type": "TEXT",
            "type": "object"
        },
        "name": {
            "nullable": False,
            "unique": False,
            "postgres_type": "TEXT",
            "type": "object"},
        "timestamp": {
            "nullable": False,
            "unique": False,
            "postgres_type": "TIMESTAMP",
            "type": "datetime64[ns, UTC]"
        },
        "open": {
            "nullable": True,
            "unique": False,
            "postgres_type": "INTEGER",
            "type": "int64"},
        "high": {
            "nullable": True,
            "unique": False,
            "postgres_type": "FLOAT",
            "type": "float64"
            },
        "low": {
            "nullable": True,
            "unique": False,
            "postgres_type": "FLOAT",
            "type": "float64"
            },
        "close": {
            "nullable": True,
            "unique": False,
            "postgres_type": "FLOAT",
            "type": "float64"
            },
        "volume": {
            "nullable": True,
            "unique": False,
            "postgres_type": "INTEGER",
            "type": "int64"
            },
        "trade_count": {
            "nullable": True,
            "unique": False,
            "postgres_type": "INTEGER",
            "type": "int64"
            },
        "vwap": {
            "nullable": True,
            "unique": False,
            "postgres_type": "FLOAT",
            "type": "float64"
            }
        }
}

root_logger.info(f"STARTED SCRIPT: {LOG_NAME}")
print(f"STARTED SCRIPT: {LOG_NAME}")

root_logger.info(f"Current Time: {str(current_time)}")
print(f"Current Time: {str(current_time)}")

if DEBUG == "1":
    pg_user = pg_user_dev
    pg_pass = pg_pass_dev
    pg_host = pg_host_dev
    pg_port = pg_port_dev
    pg_db = pg_db_dev
else:
    pg_user = pg_user_prod
    pg_pass = pg_pass_prod
    pg_host = pg_host_prod
    pg_port = pg_port_prod
    pg_db = pg_db_prod

con = psycopg2.connect(user = pg_user, password = pg_pass,
                       host= pg_host, port = pg_port,
                      database = pg_db)

# Get the latest stock prices updated date so we can fetch prices after that date
get_latest_stock_prices_sql = '''
SELECT *
FROM stock_trading_marketplace.stock_prices a
INNER JOIN (
    SELECT symbol, MAX(timestamp) AS timestamp
    FROM stock_trading_marketplace.stock_prices
    GROUP BY symbol
) b ON a.symbol = b.symbol AND a.timestamp = b.timestamp
'''

latest_stocks_df = psql.read_sql(get_latest_stock_prices_sql, con)


crypto_list =[{"symbol": "BTCUSD", "name": "Bitcoin"},
             {"symbol": "BCHUSD", "name": "Bitcoin Cash"},
             {"symbol": "ETHUSD", "name": "Ethereum"},
             {"symbol": "LTCUSD", "name": "Litecoin"}]

stock_list =[{"symbol": "TSLA", "name": "Tesla"},
             {"symbol": "AAPL", "name": "Apple"},
             {"symbol": "AMZN", "name": "Amazon"},
             {"symbol": "MSFT", "name": "Microsoft"},
             {"symbol": "NIO", "name": "Nio"},
             {"symbol":"NVDA", "name": "Nvidia"},
             {"symbol": "MRNA", "name": "Moderna"},
             {"symbol": "NKLA", "name": "Nikola"},
             {"symbol": "FB", "name": "Facebook"},
             {"symbol": "AMD", "name": "AMD"},
             {"symbol": "UBER", "name": "Uber"},
             {"symbol": "NFLX", "name": "Netflix"},
             {"symbol": "ADBE", "name": "Adobe"},
             {"symbol": "CRM", "name": "Salesforce"},
             {"symbol": "DIS", "name": "Disney"},
             {"symbol": "JP", "name": "JP Morgan"},
             {"symbol": "MA", "name": "Mastercard"},
             {"symbol": "F", "name": "Ford Motors"},
             {"symbol": "GME", "name": "GameStop"},
             {"symbol": "SHOP", "name": "Shopify"}]

latest_stock_time = latest_stocks_df['timestamp'].max().iloc[0]
latest_stock_time = latest_stock_time.replace(tzinfo=timezone.utc)

root_logger.info(f"Current Latest Stock Time: {latest_stock_time}")
print(f"Current Latest Stock Time: {latest_stock_time}")

# We want to fetch all stocks from after the latest stock time, we set it 150 minutes in the past in case
# the latest stock pull has been very recent
start_time = latest_stock_time - timedelta(minutes = 150)

# Want to pull data for the next 24 hours
end_time = start_time + timedelta(hours=24)

# Set the current time as 20 minutes in the past since the API restricts any calls within the past 15 minutes
current_time = current_time - timedelta(minutes = 20)

# If the next 24 hours is later than the current time, we only pull stocks up to the current time
if (end_time > current_time):
    end_time = current_time

# Function to fetch stocks from Alpaca API
def get_stocks(stock_symbol, start_time, end_time):
    # Get API instance
    api = REST(key_id=APCA_API_KEY_ID, secret_key=APCA_API_SECRET_KEY)
    # Fetch stock prices
    stock_prices = api.get_bars(symbol=stock_symbol, timeframe=TimeFrame.Hour, start=start_time.isoformat(),
                                end=end_time.isoformat(), adjustment='raw').df
    stock_prices = stock_prices.reset_index()
    latest_stocks = stock_prices.sort_index(ascending=False).to_dict(orient='records')
    return latest_stocks

# Function to fetch cryptocurrencies from Alpaca API
def get_latest_crypto(crypto_symbol):
    # Get API instance
    api = REST(key_id=APCA_API_KEY_ID, secret_key=APCA_API_SECRET_KEY)
    # Fetch stock prices
    stock_prices = api.get_crypto_bars(symbol=crypto_symbol, timeframe=TimeFrame.Hour, start=start_time.isoformat(),
                                end=None, exchanges = ["CBSE"]).df
    stock_prices = stock_prices.reset_index()
    stock_prices = stock_prices.drop(columns = ["exchange"])
    latest_stocks = stock_prices.sort_index(ascending=False).to_dict(orient='records')

    return latest_stocks

stock_data = []

# Fetch prices of stocks and cryptocurrencies

for stock in crypto_list:
    time.sleep(1)
    symbol = stock["symbol"]
    name = stock["name"]
    try:
        # Append the stock symbol and name to the results
        res = get_latest_crypto(symbol)
        for x in res:
            x["symbol"] = symbol
            x["name"] = name
    except Exception as e:
        print(f"Exception pulling crypto stock {symbol}: {e}")
        res = []
    stock_data.append(res)

for stock in stock_list:
    time.sleep(1)
    symbol = stock["symbol"]
    name = stock["name"]
    try:
        res = get_stocks(stock_symbol = symbol, start_time = start_time, end_time = end_time)
        # Append the stock symbol and name to the results
        for x in res:
            x["symbol"] = symbol
            x["name"] = name
    except Exception as e:
        print(f"Exception pulling stock {symbol}: {e}")
        root_logger.info(f"Exception pulling stock {symbol}: {e}")
        res = []
    stock_data.append(res)

stock_data = [x for y in stock_data for x in y]

# Insert all of the stock data into the database
cur = con.cursor()
for row in stock_data:
    symbol = stock["symbol"]
    sql_command = insert_row_query(
        row = row,
        table_name = "stock_trading_marketplace.stock_prices",
        schema = stock_prices_schema)
    try:
        cur.execute(sql_command)
        con.commit()
    except Exception as e:
        cur.execute("rollback")
        print(f"Exception inserting {symbol} into database: {e}")
        root_logger.info(f"Exception inserting {symbol} into database: {e}")


# Check the latest stocks updated date to see if api pull and updates were done successfully
new_latest_stocks_df = psql.read_sql(get_latest_stock_prices_sql, con)

new_latest_stock_time = new_latest_stocks_df['timestamp'].max().iloc[0]
new_latest_stock_time = new_latest_stock_time.replace(tzinfo=timezone.utc)
root_logger.info(f"New Latest Stock Time: {latest_stock_time}")
print(f"New Latest Stock Time: {latest_stock_time}")

cur.close()
con.close()

root_logger.info("ENDED SCRIPT. Finished Successfully")
print("ENDED SCRIPT. Finished Successfully")

### Cron Job to Execute Updated Hourly ###
# 25,55 * * * * cd "/Users/filipstoja/Desktop/Python Projects/stock_trading_marketplace/postgres_database" &&
# "/Users/filipstoja/opt/anaconda3/envs/stock_trading_marketplace/bin/python3"  scheduled_stock_prices_api_pull.py
# >> ~/cron.log 2>&1