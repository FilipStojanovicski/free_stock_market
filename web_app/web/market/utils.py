import decimal
# Function that rounds numerical data to set number of decimal places
def round_data(data, decimal_places=2, rounding_type=None):
    if data is not None:
        data = decimal.Decimal(data)
        if rounding_type == "ROUND_UP":
            rounding_type = decimal.ROUND_UP
        elif rounding_type == "ROUND_DOWN":
            rounding_type = decimal.ROUND_DOWN
        exp = decimal.Decimal('.1') ** decimal_places
        data = data.quantize(exp, rounding=rounding_type)
        data = float(data)
    return data

def format_numbers(data):
    return '{:,}'.format(data)

all_stock_crypto_list =[{"symbol": "BTCUSD", "name": "Bitcoin"},
             {"symbol": "BCHUSD", "name": "Bitcoin Cash"},
             {"symbol": "ETHUSD", "name": "Ethereum"},
             {"symbol": "LTCUSD", "name": "Litecoin"},
             {"symbol": "TSLA", "name": "Tesla"},
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
