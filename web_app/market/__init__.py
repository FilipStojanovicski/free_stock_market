from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from market.utils import round_data, format_numbers
import sys
sys.path.append('../')
from config import (DEBUG, DEV_DB, PROD_DB, FLASK_SECRET_KEY)
import os

app = Flask(__name__)

os.environ["DEBUG"] = DEBUG

if os.environ.get('DEBUG') == '1':
    print(DEV_DB)
    app.config['SQLALCHEMY_DATABASE_URI'] = DEV_DB
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = PROD_DB

app.config['SECRET_KEY'] = FLASK_SECRET_KEY
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message_category = 'info'

# Custom functions for use in Jinja
@app.context_processor
def utility_processor():
    # Function that rounds data second decimal place
    round_data
    return dict(round_data=round_data)
@app.context_processor
def utility_processor_2():
    # Function that formats numbers seperating every thousand with a comma
    format_numbers
    return dict(format_numbers=format_numbers)

from market import routes
