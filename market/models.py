from market import db, login_manager
from market import bcrypt
from flask_login import UserMixin
from market.utils import round_data, all_stock_crypto_list
from sqlalchemy import UniqueConstraint
import decimal

class StockPrices(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    symbol = db.Column(db.String(length = 30), nullable = False)
    name = db.Column(db.String(length = 100), nullable = False)
    timestamp = db.Column(db.DateTime(), nullable = False)
    open = db.Column(db.Float())
    high = db.Column(db.Float())
    low = db.Column(db.Float())
    close = db.Column(db.Float())
    volume = db.Column(db.Integer())
    trade_count = db.Column(db.Integer())
    vwap = db.Column(db.Float())
    __table_args__ = (UniqueConstraint('symbol', 'timestamp', name='_symbol_timestamp_uc'),
                     {"schema":"stock_trading_marketplace"})
    def __repr__(self):
        return f'StockPrices: {str(self.timestamp)}'

    # Formatted versions of the numerical data for display
    @property
    def prettier_open(self):
        return '{:,}'.format(self.open)
    @property
    def prettier_high(self):
        return '{:,}'.format(self.high)
    @property
    def prettier_low(self):
        return '{:,}'.format(self.low)
    @property
    def prettier_close(self):
        return '{:,}'.format(self.close)
    @property
    def prettier_volume(self):
        return '{:,}'.format(self.volume)
    @property
    def prettier_trade_count(self):
        return '{:,}'.format(self.trade_count)
    @property
    def prettier_vwap(self):
        return '{:,}'.format(self.vwap)
    @property
    def prettier_buy_unit_price(self):
        rounded_price = round_data(self.vwap, decimal_places=2, rounding_type="ROUND_UP")
        return '{:,}'.format(rounded_price)
    @property
    def prettier_sell_unit_price(self):
        rounded_price = round_data(self.vwap, decimal_places=2, rounding_type="ROUND_DOWN")
        return '{:,}'.format(rounded_price)

    def buy(self, user, quantity):
        stock_to_purchase = self.symbol
        purchase_price = (quantity * self.vwap)
        purchase_price = round_data(purchase_price, decimal_places=2, rounding_type="ROUND_UP")
        user.budget -= purchase_price
        # Want to update a users owned stocks portfolio with the new stock quantity
        user_owned_stocks = user.stocks
        owned_stock_quantity = user_owned_stocks.get_quantity(stock_to_purchase)
        user_owned_stocks.set_quantity(stock_to_purchase, owned_stock_quantity + quantity)
        # Need to update their net worth as well
        user_owned_stocks.update_owned_stocks_net_worth()
        db.session.commit()

    def sell(self, user, quantity):
        stock_to_sell = self.symbol
        sold_price = (quantity * self.vwap)
        sold_price = round_data(sold_price, decimal_places=2, rounding_type="ROUND_DOWN")
        user.budget += sold_price
        user_owned_stocks = user.stocks
        # Want to update a users owned stocks portfolio with the new stock quantity
        owned_stock_quantity = user_owned_stocks.get_quantity(stock_to_sell)
        user_owned_stocks.set_quantity(stock_to_sell, owned_stock_quantity - quantity)
        # Need to update their net worth as well
        user_owned_stocks.update_owned_stocks_net_worth()
        db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Users(db.Model, UserMixin):
    __table_args__ = {"schema":"stock_trading_marketplace"}
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length = 30), nullable = False, unique = True)
    stocks = db.relationship('OwnedStocks', backref='owned_user', lazy=True, uselist = False)
    email_address = db.Column(db.String(length = 50), nullable = False, unique = True)
    password_hash = db.Column(db.String(length = 60), nullable = False)
    company = db.Column(db.String(length = 30), nullable = False)
    budget = db.Column(db.Float(), nullable=False, default=100000)
    def __repr__(self):
        return f'User {self.username}'

    @property
    def prettier_budget(self):
        rounded_budget = round_data(self.budget, decimal_places=2, rounding_type="ROUND_DOWN")
        return '{:,}'.format(rounded_budget)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

    # If a user has enough budget they can purchase the stock quantity
    def can_purchase(self, purchased_stock_object, purchased_quantity):
        purchase_price = (purchased_quantity * purchased_stock_object.vwap)
        purchase_price = round_data(purchase_price, decimal_places=2, rounding_type="ROUND_UP")
        return self.budget >= purchase_price

    # If a user has enough of the owned stock in their portfolio they can sell it
    def can_sell(self, sold_stock_object, sold_quantity):
        stock_to_sell = sold_stock_object.symbol
        user_owned_stocks = self.stocks
        owned_stock_quantity = user_owned_stocks.get_quantity(stock_to_sell)
        return owned_stock_quantity >= sold_quantity

    # If a user has enough of the owned stock in their portfolio they can sell it
    def get_net_worth(self):
        budget = self.budget
        user_owned_stocks = self.stocks
        net_worth = budget + user_owned_stocks.net_worth
        net_worth = round_data(net_worth, decimal_places=2, rounding_type="ROUND_DOWN")
        return net_worth


class OwnedStocks(db.Model):
    __table_args__ = {"schema":"stock_trading_marketplace"}
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length = 30), nullable = False, unique = True)
    owner = db.Column(db.Integer(), db.ForeignKey('stock_trading_marketplace.users.id'))
    net_worth = db.Column(db.Float(), nullable = False, default = 0)
    tsla = db.Column(db.Float(), nullable = False, default = 0)
    aapl = db.Column(db.Float(), nullable = False, default = 0)
    amzn = db.Column(db.Float(), nullable = False, default = 0)
    msft = db.Column(db.Float(), nullable = False, default = 0)
    nio = db.Column(db.Float(), nullable = False, default = 0)
    nvda = db.Column(db.Float(), nullable = False, default = 0)
    mrna = db.Column(db.Float(), nullable = False, default = 0)
    nkla = db.Column(db.Float(), nullable = False, default = 0)
    fb = db.Column(db.Float(), nullable = False, default = 0)
    amd = db.Column(db.Float(), nullable = False, default = 0)
    uber = db.Column(db.Float(), nullable = False, default = 0)
    nflx = db.Column(db.Float(), nullable = False, default = 0)
    adbe = db.Column(db.Float(), nullable = False, default = 0)
    crm = db.Column(db.Float(), nullable = False, default = 0)
    dis = db.Column(db.Float(), nullable = False, default = 0)
    jp = db.Column(db.Float(), nullable = False, default = 0)
    ma = db.Column(db.Float(), nullable = False, default = 0)
    f = db.Column(db.Float(), nullable = False, default = 0)
    gme = db.Column(db.Float(), nullable = False, default = 0)
    shop = db.Column(db.Float(), nullable = False, default = 0)
    btcusd = db.Column(db.Float(), nullable = False, default = 0)
    bchusd = db.Column(db.Float(), nullable = False, default = 0)
    ethusd = db.Column(db.Float(), nullable = False, default = 0)
    ltcusd = db.Column(db.Float(), nullable = False, default = 0)

    def __repr__(self):
        return f'OwnedStocks: {self.username}'

    # Change the symbol using a string
    def set_quantity(self, symbol, quantity):
        col_name = str(symbol).lower()
        setattr(self, col_name, quantity)

    # Access the symbol using a string
    def get_quantity(self, symbol):
        col_name = str(symbol).lower()
        current_quantity = getattr(self, col_name)
        return current_quantity

    def get_prettier_quantity(self, symbol):
        col_name = str(symbol).lower()
        current_quantity = getattr(self, col_name)
        rounded_quantity= round_data(current_quantity, decimal_places=2, rounding_type="ROUND_DOWN")
        return '{:,}'.format(rounded_quantity)

    # Get all of the owned stocks with quantity greater than zero
    def get_all_owned_stocks(self):
        owned_stocks = []
        for row in sorted(all_stock_crypto_list, key=lambda d: d['symbol']):
            stock = row["symbol"]
            quantity = self.get_quantity(stock)
            quantity = round_data(quantity, decimal_places=2, rounding_type="ROUND_DOWN")
            if quantity > 0:
                owned_stocks.append(stock)
        return owned_stocks

    # Get the total value of all owned stocks
    def get_owned_stocks_net_worth(self):
        total_value = 0
        for row in all_stock_crypto_list:
            stock = row["symbol"]
            quantity = self.get_quantity(stock)
            stock_price_object = self.get_symbol_stock_price_object(stock)
            total_value += (quantity * stock_price_object.vwap)
        return total_value

    # Update the total value of all owned stocks
    def update_owned_stocks_net_worth(self):
        net_worth = self.get_owned_stocks_net_worth()
        self.net_worth = net_worth
        db.session.commit()

    # Get the stock price object associated with a symbol
    def get_symbol_stock_price_object(self, symbol):
        stock_price_object = StockPrices.query.filter_by(symbol=symbol.upper()).order_by(StockPrices.timestamp.desc()).first()
        return stock_price_object
