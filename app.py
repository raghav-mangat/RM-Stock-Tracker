"""
RM-Stock-Tracker

RM Stock Tracker is a production-grade web application for exploring
U.S. stocks, analyzing market data, and managing personalized watchlist
with alerts. The platform is designed with a strong focus on
performance, usability, scalability, and clean backend architecture.

Live Website: https://www.rmstocktracker.com

Created By: Raghav Mangat
Started On: June 07, 2025
"""

import os
from flask import (
    Flask, render_template, request, session, redirect, url_for,
    flash, jsonify, has_request_context, send_from_directory, g
)
from dotenv import load_dotenv
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import limiter
from logging_config import setup_logging
from metrics import init_metrics
from metrics.middleware import register_metrics_middleware
from authlib.integrations.flask_client import OAuth
import uuid
from datetime import datetime
from redis import Redis
from rq import Queue
from models.database import db
from admin import admin_bp
from auth import auth_bp
from watchlist import watchlist_bp
from utils.filters import register_custom_filters
from utils.error_handlers import register_error_handlers
from utils.breadcrumbs import generate_breadcrumbs
from utils.status_files import db_last_updated, db_last_updated_date
from utils.market_status import get_market_status_with_time_ago
from utils.db_queries.tables.dataset_version import get_active_dataset_id
from utils.db_queries.all_indices import get_all_indices
from utils.db_queries.show_index import get_index_data
from utils.db_queries.all_stocks import (
    get_ticker_tape_stocks, get_trending_stocks, get_top_stocks_categories,
    db_get_top_stocks_data
)
from utils.db_queries.query_stocks import get_query_stocks
from utils.db_queries.show_stock import (
    get_stock_data, get_chart_data, get_timeframe_options, verify_ticker
)
from utils.db_queries.user_data import get_user_by_id
from utils.db_queries.watchlist import get_all_user_folders

# Load environment variables
load_dotenv()

# Initialize the Flask App
app = Flask(__name__)

# Configure the Flask App Secret Key
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Initialize Custom Flask App Config depending on the ENV
if os.getenv("FLASK_APP_ENV") == "dev":
    app.config.from_object("config.DevConfig")
    app.config["STATUS_FILES_DIR"] = os.path.join(app.root_path, "status_files")
    app.config["DATA_FILES_DIR"] = os.path.join(app.root_path, "data_files")
else:
    app.config.from_object("config.ProdConfig")

# To get the users' correct IP address
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1
)

# Required for generating absolute URLs (url_for with _external=True)
# outside request context (e.g. emails, cron jobs)
app.config["SERVER_NAME"] = os.getenv("SERVER_NAME")
app.config["PREFERRED_URL_SCHEME"] = os.getenv("PREFERRED_URL_SCHEME")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 280,
    'pool_size': 5,
    'max_overflow': 0
}

# Initialize the database
db.init_app(app)

# Initialize the Flask Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# Initialize Selected Email Provider
app.config["EMAIL_PROVIDER"] = os.getenv("EMAIL_PROVIDER", "smtp")

# Initialize Email Provider - Mailgun
app.config["MAILGUN_API_KEY"] = os.getenv("MAILGUN_API_KEY")
app.config["MAILGUN_BASE_URL"] = os.getenv("MAILGUN_BASE_URL")
app.config["MAILGUN_DOMAIN"] = os.getenv("MAILGUN_DOMAIN")
app.config["MAILGUN_VERSION"] = os.getenv("MAILGUN_VERSION")
app.config["MAILGUN_ENDPOINT"] = os.getenv("MAILGUN_ENDPOINT")
app.config["MAILGUN_DEFAULT_SENDER"] = os.getenv("MAILGUN_DEFAULT_SENDER")

# Initialize Flask Mail, SMTP - Namecheap or Gmail
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = os.getenv("MAIL_PORT")
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS")
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

# Initialize Flask Limiter
limiter.init_app(app)

# Initialize Flask-WTF CSRF Protection
csrf = CSRFProtect(app)

# Initialize OAuth
oauth = OAuth(app)

# Register Sign In with Google
app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY = "https://accounts.google.com/.well-known/openid-configuration"
oauth.register(
    name="google",
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url=GOOGLE_DISCOVERY,
    client_kwargs={"scope": "openid email profile"}
)
app.config["OAUTH"] = oauth

# Redis Connection and Email Queues
redis_conn = Redis.from_url(os.getenv("REDIS_CONNECTION_URL"))
email_high_queue = Queue("emails_high", connection=redis_conn) # High priority
email_low_queue = Queue("emails_low", connection=redis_conn) # Low priority
app.config["REDIS"] = redis_conn

# Setup Logging
setup_logging(app)

# Setup Metrics
init_metrics(app)
register_metrics_middleware(app)

# Access Flask App
def get_app():
    return app

# Register the Flask Blueprints
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(watchlist_bp, url_prefix="/watchlist")

# Register custom filters
register_custom_filters(app)

# Register error handlers
register_error_handlers(app)

# Make breadcrumbs available to all templates
@app.context_processor
def inject_breadcrumbs():
    # Breadcrumbs are only available during an active HTTP request
    if not has_request_context():
        return {}
    return {'breadcrumbs': generate_breadcrumbs()}

# Make current year available to all templates
@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}

# Make sure the session is secure and up to date before every request
@app.before_request
def enforce_session_security():
    if request.endpoint in (
        "auth.signup",
        "auth.login",
        "auth.google_signin",
        "auth.google_signin_callback",
        "auth.logout",
    ):
        return None

    if not current_user.is_authenticated:
        return None

    session_timestamp = session.get("security_timestamp")
    if not session_timestamp:
        flash(
            "Invalid session. Please log in again.",
            "danger"
        )
        return redirect(url_for("auth.logout"))

    if session_timestamp != current_user.security_timestamp:
        flash(
            "Your session expired. Please log in again.",
            "warning"
        )
        return redirect(url_for("auth.logout"))
    return None

# Make sure the request id is attached before every request
@app.before_request
def attach_request_id():
    # Gives a unique id to each request
    g.request_id = uuid.uuid4().hex[:12]


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
        last_updated=last_updated,
        market_status=get_market_status_with_time_ago()
    )

@app.route("/indices/<string:index_id>")
def show_index(index_id):
    sort_by = request.args.get("sort_by", "name")
    order = request.args.get("order", "asc")
    filter_by = request.args.getlist("filter")

    index_data = get_index_data(index_id, sort_by, order, filter_by)

    return render_template(
        "show_index.html",
        index=index_data.get("index"),
        index_data=index_data.get("index_data"),
        filter_colors=index_data.get("filter_colors"),
        sort_dropdown_options=index_data.get("sort_dropdown_options"),
        sort_by=sort_by,
        order=order,
        market_status=get_market_status_with_time_ago()
    )

@app.route("/stocks")
def all_stocks():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    dataset_version_id = get_active_dataset_id()

    ticker_tape_stocks = get_ticker_tape_stocks(dataset_version_id)
    trending_stocks = get_trending_stocks(dataset_version_id)
    top_stocks_categories = get_top_stocks_categories(dataset_version_id)

    return render_template(
        "all_stocks.html",
        last_updated=last_updated,
        market_status=get_market_status_with_time_ago(),
        ticker_tape_stocks=ticker_tape_stocks,
        trending_stocks=trending_stocks,
        top_stocks_categories=top_stocks_categories
    )

@app.route("/get-top-stocks-data/<string:category>")
def get_top_stocks_data(category):
    dataset_version_id = get_active_dataset_id()

    gainers = render_template(
        "partials/top_stocks_table_data.html",
        stocks_type="gainers",
        stocks=db_get_top_stocks_data(category, "gainers", dataset_version_id)
    )
    losers = render_template(
        "partials/top_stocks_table_data.html",
        stocks_type="losers",
        stocks=db_get_top_stocks_data(category, "losers", dataset_version_id)
    )
    top_traded = render_template(
        "partials/top_stocks_table_data.html",
        stocks_type="top_traded",
        stocks=db_get_top_stocks_data(category, "top_traded", dataset_version_id)
    )

    html = {
        "gainers": gainers,
        "losers": losers,
        "top_traded": top_traded
    }
    return jsonify({"html": html})

@app.route("/query-stocks")
def query_stocks():
    query = request.args.get("q", "")
    return get_query_stocks(query)

@app.route("/stocks/<string:ticker>")
def show_stock(ticker):
    canonical_ticker = ticker.strip().upper()

    if ticker != canonical_ticker:
        return redirect(
            url_for("show_stock", ticker=canonical_ticker),
            code=301
        )

    ticker_master, stock_master, stock_detail = verify_ticker(ticker)
    now = db_last_updated_date()

    stock_data = get_stock_data(ticker_master, stock_master, stock_detail, now)

    timeframe_options = get_timeframe_options()
    initial_timeframe = timeframe_options[0]
    initial_stock_chart_data = get_chart_data(initial_timeframe, stock_master, now)

    user_folders = []
    if current_user.is_authenticated:
        user_folders = get_all_user_folders(current_user)

    return render_template(
        "show_stock.html",
        stock=stock_data,
        timeframe_options=timeframe_options,
        initial_timeframe=initial_timeframe,
        initial_stock_chart_data=initial_stock_chart_data,
        user_folders=user_folders,
        market_status=get_market_status_with_time_ago()
    )

@app.route("/chart-data")
def chart_data():
    ticker = request.args.get("ticker", "").strip().upper()

    ticker_master, stock_master, stock_detail = verify_ticker(ticker)
    now = db_last_updated_date()

    timeframe = request.args.get("timeframe", "").strip()
    data = get_chart_data(timeframe, stock_master, now)
    return data

@app.route("/about")
def about():
    return render_template("legal/about.html")

@app.route("/privacy")
def privacy():
    last_updated_at = app.config["LEGAL_LAST_UPDATED_AT"]
    return render_template(
        "legal/privacy.html",
        last_updated_at=last_updated_at
    )

@app.route("/terms")
def terms():
    last_updated_at = app.config["LEGAL_LAST_UPDATED_AT"]
    return render_template(
        "legal/terms.html",
        last_updated_at=last_updated_at
    )

@app.route("/robots.txt")
def robots_txt():
    return send_from_directory(
        directory=app.static_folder,
        path="assets/robots.txt",
        mimetype="text/plain"
    )

@app.route("/sitemap.xml", methods=["GET"])
def sitemap():
    pages = [
        {
            "loc": url_for("home", _external=True),
            "changefreq": "weekly",
            "priority": "1.0",
        },
        {
            "loc": url_for("all_stocks", _external=True),
            "changefreq": "daily",
            "priority": "0.9",
        },
        {
            "loc": url_for("all_indices", _external=True),
            "changefreq": "weekly",
            "priority": "0.8",
        },
        {
            "loc": url_for("watchlist.index", _external=True),
            "changefreq": "daily",
            "priority": "0.9",
        },
        {
            "loc": url_for("auth.login", _external=True),
            "changefreq": "monthly",
            "priority": "0.5",
        },
        {
            "loc": url_for("auth.signup", _external=True),
            "changefreq": "monthly",
            "priority": "0.5",
        },
        {
            "loc": url_for("about", _external=True),
            "changefreq": "monthly",
            "priority": "0.2",
        },
        {
            "loc": url_for("privacy", _external=True),
            "changefreq": "yearly",
            "priority": "0.2",
        },
        {
            "loc": url_for("terms", _external=True),
            "changefreq": "yearly",
            "priority": "0.2",
        }
    ]

    return render_template("xml/sitemap.xml", pages=pages), {
        "Content-Type": "application/xml"
    }


if __name__ == "__main__":
    app.logger.info(
        "Starting Flask App",
        extra={"log_type": "system", "action": "start_flask_app"}
    )
    app.run()
