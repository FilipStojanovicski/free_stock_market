from market import app
from flask import render_template, redirect, url_for, flash, request
from market.models import StockPrices, Users, OwnedStocks
from market.forms import RegisterForm, LoginForm, PurchaseStockForm, SellStockForm
from market import db
from flask_login import login_user, logout_user, login_required, current_user
from market.utils import round_data, format_numbers, all_stock_crypto_list
import sqlalchemy
from sqlalchemy.sql.expression import func


@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/market', methods = ['GET', 'POST'])
@login_required
def market_page():
    # Want to fill the market page with the latest stock data

    # Get all Users and their Net Worths

    # Get a subquery with the latest timestamp for each symbol
    latest_stocks_subquery = db.session.query(StockPrices.symbol, func.max(StockPrices.timestamp).label(
        "timestamp")).group_by(StockPrices.symbol).subquery()
    # Merge stocks back onto the maximum timestamp
    latest_stocks = db.session.query(StockPrices).join(
        latest_stocks_subquery, (StockPrices.symbol == latest_stocks_subquery.c.symbol) & (
                StockPrices.timestamp == latest_stocks_subquery.c.timestamp)).all()

    purchase_form = PurchaseStockForm()
    selling_form = SellStockForm()

    if request.method == "POST":
        if purchase_form.validate_on_submit():
            purchased_stock = request.form.get("purchased_stock")
            purchased_quantity = purchase_form.quantity.data
            purchased_stock_object = StockPrices.query.filter_by(symbol=purchased_stock).first()

            if purchased_stock_object:
                if current_user.can_purchase(purchased_stock_object, purchased_quantity):
                    purchase_price = (purchased_quantity * purchased_stock_object.vwap)
                    purchase_price = purchase_price
                    purchase_price = round_data(purchase_price, decimal_places=2, rounding_type="ROUND_UP")
                    purchased_stock_object.buy(user=current_user, quantity=purchased_quantity)
                    db.session.commit()
                    flash(f"Congratulations you purchased {format_numbers(purchased_quantity)} units of {purchased_stock} stock for ${format_numbers(purchase_price)}",
                      category="success")
                else:
                    flash(f"Unfortunately you don't have enough money to purchase {format_numbers(purchased_quantity)} units of {purchased_stock} stock",
                      category="danger")

        if selling_form.validate_on_submit():
            sold_stock = request.form.get("sold_stock")
            sold_quantity = selling_form.quantity.data
            sold_stock_object = StockPrices.query.filter_by(symbol=sold_stock).first()

            if sold_stock_object:
                if current_user.can_sell(sold_stock_object, sold_quantity):
                    sold_price = (sold_quantity * sold_stock_object.vwap)
                    sold_price = round_data(sold_price, decimal_places=2, rounding_type="ROUND_DOWN")
                    sold_stock_object.sell(user=current_user, quantity=sold_quantity)
                    db.session.commit()
                    flash(f"Congratulations you sold {format_numbers(sold_quantity)} units of {sold_stock} stock for ${format_numbers(sold_price)}",
                      category="success")
                else:
                    flash(f"Unfortunately you don't have {format_numbers(sold_quantity)} units of {sold_stock} stock to sell",
                      category="danger")

        if purchase_form.errors != {}:
            for err_msg in purchase_form.errors.values():
                flash(f"There was an error with purchasing the stock: {err_msg}", category="danger")

        if selling_form.errors != {}:
            for err_msg in selling_form.errors.values():
                flash(f"There was an error with selling the stock: {err_msg}", category="danger")

        return redirect((url_for('market_page')))

    if request.method == "GET":
        owned_stocks_object = current_user.stocks
        return render_template('market.html', stocks = latest_stocks, purchase_form = purchase_form,
                               owned_stocks = owned_stocks_object, selling_form = selling_form)

@app.route('/register', methods = ['GET', 'POST'])
def register_page():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        user_to_create = Users(
            username = register_form.username.data,
            email_address = register_form.email_address.data,
            password = register_form.password1.data,
            company = register_form.company.data,
            budget = 100000)
        # Want to create a portfolio of their owned stocks at the same time when we create new user
        owned_stocks_to_create = OwnedStocks(
            username = user_to_create.username,
            owned_user = user_to_create)
        db.session.add(user_to_create)
        db.session.add(owned_stocks_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are now logged in as {user_to_create.username}", category='success')
        return redirect(url_for('market_page'))
    if register_form.errors != {}:
        for err_msg in register_form.errors.values():
            flash(f"There was an error with creating a user: {err_msg}", category="danger")

    return render_template('register.html', register_form = register_form)

@app.route('/login', methods =['GET','POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = Users.query.filter_by(username = form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category = 'success')
            return redirect(url_for('market_page'))
        else:
            flash('Username and password do not match! Please try again.', category='danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/leaderboard')
def leaderboard_page():
    # Get total users
    num_users = Users.query.count()

    # Get all Users and their Net Worths
    users_net_worths = db.session.query(Users).join(Users.stocks).add_entity(OwnedStocks)

    # Add the users budget to their owned stocks net worth to get total net worth
    users_net_worths = users_net_worths.add_column((Users.budget + OwnedStocks.net_worth).label("total_net_worth"))
    # Order by total net worth and assign a rank
    users_net_worths = users_net_worths.add_column(func.row_number().over(
        order_by=sqlalchemy.desc((Users.budget + OwnedStocks.net_worth))).label('rank'))

    if current_user.is_authenticated:
        # Get current user net worth
        current_user_net_worth = users_net_worths.filter(Users.id == current_user.id).first()
    else:
        current_user_net_worth = None

    # Get Top 20 Users by net worth
    top_users_net_worths = users_net_worths.order_by(sqlalchemy.desc("total_net_worth")).limit(20).all()

    return render_template('leaderboard.html', users_net_worths = top_users_net_worths, num_users = num_users,
                           current_user_net_worth = current_user_net_worth)