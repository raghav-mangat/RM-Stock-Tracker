from flask import jsonify
import random
from models.database import db, StockMaster
from utils.db_queries.all_stocks import get_stocks_popularity
from utils.constants import NUM_SUGGESTIONS

def get_query_stocks(user_query):
    popularity = get_stocks_popularity()

    db_base_query = db.session.query(
        StockMaster.ticker,
        StockMaster.name,
    ).order_by(
        popularity.desc()
    )

    if user_query:
        # User typed something
        user_query_upper = user_query.upper()
        matches = (
            db_base_query
            .filter(
                StockMaster.ticker.ilike(f"{user_query_upper}%") |
                StockMaster.name.ilike(f"{user_query}%")
            )
        )
        matches = matches.limit(NUM_SUGGESTIONS).all()
    else:
        # Empty user query, return popular stocks
        matches = db_base_query
        matches = matches.limit(NUM_SUGGESTIONS).all()
        random.shuffle(matches)

    return jsonify([
        {"ticker": match.ticker, "name": match.name}
        for match in matches
    ])