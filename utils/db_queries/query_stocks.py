from flask import jsonify
from sqlalchemy import func
from models.database import db, StockMaster
from utils.constants import NUM_SUGGESTIONS

def get_query_stocks(query):
    # Estimate popularity using (day close price) * volume
    popularity = (
        func.coalesce(StockMaster.day_close, 0) *
        func.coalesce(StockMaster.volume, 0)
    )

    base_query = (
        db.session.query(
            StockMaster.ticker,
            StockMaster.name
        ).order_by(popularity.desc())
    )

    if query:
        # User typed something
        query_upper = query.upper()
        matches = (
            base_query
            .filter(
                StockMaster.ticker.ilike(f"{query_upper}%") |
                StockMaster.name.ilike(f"{query}%")
            )
        )
    else:
        # Empty query, return popular stocks
        matches = base_query

    matches = matches.limit(NUM_SUGGESTIONS).all()

    return jsonify([
        {"ticker": match.ticker, "name": match.name}
        for match in matches
    ])