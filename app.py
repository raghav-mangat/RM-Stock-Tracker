"""
RM-Stock-Tracker

An informative and user-friendly web app to explore U.S. stocks and major
market indices using real-time financial data.
Built with Python, Flask, SQLAlchemy, Bootstrap, Chart.js and Polygon.io API.

Live Website: https://www.rmstocktracker.com/

Created By: Raghav Mangat
Started On: June 07, 2025
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash
from models.database import db
from utils.filters import register_custom_filters
from utils.error_handlers import register_error_handlers
from utils.breadcrumbs import generate_breadcrumbs
from utils.populate_db_info import db_last_updated
from utils.db_queries.all_indices import get_all_indices
from utils.db_queries.show_index import get_index_data
from utils.db_queries.all_stocks import get_ticker_tape_stocks, get_top_stocks
from utils.db_queries.query_stocks import get_query_stocks
from utils.db_queries.show_stock import get_stock_data, get_chart_data, get_timeframe_options
from utils.db_queries.user_data import get_user_by_id, get_user_by_email, add_new_user
from utils.forms import LoginForm, SignupForm

# Load environment variables
load_dotenv()

# Initialize the Flask App
app = Flask(__name__)

# Configure the Flask App Secret Key
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_size': 5,
    'max_overflow': 0
}

# Initialize the database
db.init_app(app)

# Initialize the Flask Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# Register custom filters
register_custom_filters(app)

# Register error handlers
register_error_handlers(app)

# Make breadcrumbs available to all templates
@app.context_processor
def inject_breadcrumbs():
    return {'breadcrumbs': generate_breadcrumbs()}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/indices")
def all_indices():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    indices = get_all_indices()

    return render_template(
        "all_indices.html",
        indices=indices,
        last_updated=last_updated
    )

@app.route("/indices/<string:index_id>")
def show_index(index_id):
    sort_by = request.args.get('sort_by')
    order = request.args.get('order')
    filter_by = request.args.getlist('filter')

    index_data = get_index_data(index_id, sort_by, order, filter_by)

    return render_template(
        "show_index.html",
        index=index_data.get("index"),
        index_data=index_data.get("index_data"),
        filter_colors=index_data.get("filter_colors"),
        sort_dropdown_options=index_data.get("sort_dropdown_options"),
        sort_by=sort_by,
        order=order,
    )

@app.route("/stocks")
def all_stocks():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    ticker_tape_stocks = get_ticker_tape_stocks()

    top_stocks = get_top_stocks()

    return render_template(
        "all_stocks.html",
        last_updated=last_updated,
        ticker_tape_stocks=ticker_tape_stocks,
        top_stocks=top_stocks
    )

@app.route("/query-stocks")
def query_stocks():
    query = request.args.get("q", "").strip()
    result = get_query_stocks(query)
    return result

@app.route("/stocks/<string:ticker>")
def show_stock(ticker):
    stock_data = get_stock_data(ticker)

    timeframe_options = get_timeframe_options()
    initial_timeframe = timeframe_options[0]
    initial_stock_chart_data = get_chart_data(ticker, initial_timeframe)

    return render_template(
        "show_stock.html",
        stock=stock_data.get("stock"),
        rel_companies=stock_data.get("rel_companies"),
        last_updated=stock_data.get("last_updated"),
        timeframe_options=timeframe_options,
        initial_timeframe=initial_timeframe,
        initial_stock_chart_data=initial_stock_chart_data,
    )

@app.route("/chart-data")
def chart_data():
    ticker = request.args.get("ticker", "").strip()
    timeframe = request.args.get("timeframe", "").strip()
    data = get_chart_data(ticker, timeframe)
    return data

@app.route('/watchlist')
def watchlist():
    return render_template("watchlist.html")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        name = form.username.data
        email = form.email.data
        password_hash = hash_and_salted_password

        user = add_new_user(
            name=name,
            email=email,
            password_hash=password_hash
        )

        flash("Account created successfully!", "success")
        login_user(user)
        return redirect(url_for('watchlist'))

    return render_template("signup.html", form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        login_user(user)
        flash("Logged in successfully!", "success")
        return redirect(url_for('watchlist'))

    return render_template("login.html", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run()
