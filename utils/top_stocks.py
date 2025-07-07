import os
import sys
from dotenv import load_dotenv
from flask import Flask

# Load environment variables from .env file
load_dotenv()

IS_RELEASE = os.getenv("IS_RELEASE")

if IS_RELEASE == "1":
    # Ensure the project root is in Python's path: in PythonAnywhere
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
elif IS_RELEASE == "0":
    # Ensure the instance folder exists for the database: in local PC
    db_uri = os.getenv("DATABASE_URI")
    if db_uri and db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)

from models.database import db, StockMaster

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
db.init_app(app)

def get_top_stocks():
    # Number of top stocks to be shown for each category
    num_top_stocks = 50

    top_stocks = {}
    with app.app_context():
        # Top Gainers
        gainers = StockMaster.query.order_by(
            StockMaster.todays_change_perc.desc()
        ).limit(num_top_stocks).all()

        # Top Losers
        losers = StockMaster.query.order_by(
            StockMaster.todays_change_perc.asc()
        ).limit(num_top_stocks).all()

        # Top Stocks traded by Volume
        top_traded = StockMaster.query.order_by(
            StockMaster.volume.desc()
        ).limit(num_top_stocks).all()

        top_stocks = {
            "gainers": gainers,
            "losers": losers,
            "top_traded": top_traded
        }

    return top_stocks