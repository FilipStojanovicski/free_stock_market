import pandas as pd
from postgres_functions import create_sql_tables_from_json, insert_row_query
import psycopg2
import datetime
from alpaca_trade_api.rest import REST, TimeFrame
import os
from config import (DEBUG, pg_user_dev, pg_pass_dev, pg_host_dev, pg_port_dev, pg_db_dev, pg_user_prod,
pg_pass_prod, pg_host_prod, pg_port_prod, pg_db_prod, APCA_API_KEY_ID, APCA_API_SECRET_KEY)
import time

# Define schemas for database table
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

users_schema = {
    "primary_key": "id",
    "schema": "stock_trading_marketplace",
    "table_name": "users",
    "fields": {
        "id": {
            "nullable": False,
            "unique": True,
            "postgres_type": "INTEGER",
            "type": "int64"},
        "username": {
            "nullable": False,
            "unique": True,
            "postgres_type": "TEXT",
            "type": "object"},
        "email_address": {
            "nullable": False,
            "unique": True,
            "postgres_type": "TEXT",
            "type": "object"},
        "password_hash": {
            "nullable": False,
            "unique": False,
            "postgres_type": "TEXT",
            "postgres_options": "",
            "type": "object"},
        "company": {
            "nullable": False,
            "unique": False,
            "postgres_type": "TEXT",
            "postgres_options": "",
            "type": "object"
            },
        "budget": {
            "nullable": False,
            "unique": False,
            "postgres_type": "FLOAT",
            "postgres_options": "",
            "type": "float64",
            "default": "10000"
        }
        },
    "table_name": "users",
    "postgres": True}

# List of cryptocurrencies and stocks
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

owned_stocks_schema = {
    "primary_key": "id",
    "schema": "stock_trading_marketplace",
    "table_name": "owned_stocks",
    "fields": {
        "id": {
            "nullable": False,
            "unique": True,
            "postgres_type": "INTEGER",
            "type": "int64"},
        "username": {
            "nullable": False,
            "unique": True,
            "postgres_type": "TEXT",
            "type": "object"
        },
        "net_worth": {
            "nullable": False,
            "unique": False,
            "postgres_type": "FLOAT",
            "default": "0",
            "type": "float64"
        }
    },
    "postgres": True}

# All of the stocks and crypto in the stock prices table will have the same field
for stock in [x["symbol"] for x in stock_list]:
    field = {"nullable": False,
             "unique": False,
             "postgres_type": "FLOAT",
             "default": "0",
             "type": "float64"}
    owned_stocks_schema["fields"][stock] = field

for stock in [x["symbol"] for x in crypto_list]:
    field = {"nullable": False,
             "unique": False,
             "postgres_type": "FLOAT",
             "default": "0",
             "type": "float64"}
    owned_stocks_schema["fields"][stock] = field

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
cur = con.cursor()

# Drop all existing tables
drop_all_tables_sql = "DROP TABLE IF EXISTS stock_trading_marketplace.owned_stocks; " + \
                      "DROP TABLE IF EXISTS stock_trading_marketplace.stock_prices; " + \
                      "DROP TABLE IF EXISTS stock_trading_marketplace.users;"
cur.execute(drop_all_tables_sql)
con.commit()

# Create schema if it doesn't exist
create_schema_sql = "CREATE SCHEMA IF NOT EXISTS stock_trading_marketplace;"
cur.execute(create_schema_sql)
con.commit()

# Create all of the tables
create_users_table_sql = create_sql_tables_from_json(users_schema)
cur.execute(create_users_table_sql)
con.commit()

stock_prices_extra_sql_args = ", UNIQUE (symbol, timestamp)"
create_stock_prices_table_sql = create_sql_tables_from_json(stock_prices_schema, stock_prices_extra_sql_args)
cur.execute(create_stock_prices_table_sql)
con.commit()

owned_stocks_extra_sql_args = ", owner INTEGER, CONSTRAINT fk_user FOREIGN KEY(owner) REFERENCES stock_trading_marketplace.users(id)"
create_owned_stocks_sql = create_sql_tables_from_json(owned_stocks_schema, owned_stocks_extra_sql_args)
cur.execute(create_owned_stocks_sql)
con.commit()

global APCA_API_KEY_ID
global APCA_API_SECRET_KEY

# Function to fetch the latest stock prices from the Alpaca API
def get_latest_stocks(stock_symbol):
    # Get API instance
    api = REST(key_id=APCA_API_KEY_ID, secret_key=APCA_API_SECRET_KEY)
    # Get latest trade object
    latest_trade = api.get_latest_trade(symbol=stock_symbol)
    # Get latest trade time
    latest_trade_time = latest_trade.t.astimezone("utc")
    # Go 24 hours before latest trade time
    start_time = latest_trade_time - datetime.timedelta(hours=24)
    # Fetch stock prices from last 24 hours on an hourly timeinterval
    stock_prices = api.get_bars(symbol=stock_symbol, timeframe=TimeFrame.Hour, start=start_time.isoformat(),
                                end=None, adjustment='raw').df
    stock_prices = stock_prices.reset_index()
    # Get latest VWAP as Price
    latest_stocks = stock_prices.sort_index(ascending=False).to_dict(orient='records')

    return latest_stocks

# Function to fetch the latest crypto prices from Alpaca API
def get_latest_crypto(crypto_symbol):
    # Get API instance
    api = REST(key_id=APCA_API_KEY_ID, secret_key=APCA_API_SECRET_KEY)
    # Get latest trade object
    latest_trade = api.get_latest_crypto_trade(symbol=crypto_symbol, exchange = ["CBSE"])
    # Get latest trade time
    latest_trade_time = latest_trade.t.astimezone("utc")
    # Go 24 hours before latest trade time
    start_time = latest_trade_time - datetime.timedelta(hours=24)
    # Fetch stock prices from last 24 hours on an hourly timeinterval
    stock_prices = api.get_crypto_bars(symbol=crypto_symbol, timeframe=TimeFrame.Hour, start=start_time.isoformat(),
                                end=None, exchanges = ["CBSE"]).df
    stock_prices = stock_prices.reset_index()
    stock_prices = stock_prices.drop(columns = ["exchange"])
    # Get latest VWAP as Price
    latest_stocks = stock_prices.sort_index(ascending=False).to_dict(orient='records')

    return latest_stocks

stock_data = []

# Fetch all stocks and cryptocurrencies

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
        # Append the stock symbol and name to the results
        res = get_latest_stocks(symbol)
        for x in res:
            x["symbol"] = symbol
            x["name"] = name
    except Exception as e:
        print(f"Exception pulling stock {symbol}: {e}")
        res = []
    stock_data.append(res)

stock_data = [x for y in stock_data for x in y]

# Insert all of the stock data into the database
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

# for row in users_data:
#     sql_command = insert_row_query(
#         row = row,
#         table_name = "stock_trading_marketplace.users",
#         schema = users_schema)
#     cur.execute(sql_command)
# con.commit()

# Check that all of the stocks were inserted succesfully
cur.execute("SELECT * FROM stock_trading_marketplace.stock_prices")
res = cur.fetchall()
print(len(res))

# cur.execute("SELECT * FROM stock_trading_marketplace.users")
# res = cur.fetchall()

# print(len(res))
# print(res[0:5])

cur.close()
con.close()


