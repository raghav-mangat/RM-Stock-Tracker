from flask import jsonify
from sqlalchemy import func
from models.database import db, StockMaster

def get_query_stocks(query):
    result = jsonify([])
    num_suggestions = 10

    if query:
        query_upper = query.upper()
        # Estimate popularity using (day close price) * volume
        popularity = func.coalesce(StockMaster.day_close, 0) * func.coalesce(StockMaster.volume, 0)

        # One combined query for both ticker and name startswith, ordered by popularity
        matches = (
            db.session.query(
                StockMaster.ticker,
                StockMaster.name
            )
            .filter(
                StockMaster.ticker.ilike(f"{query_upper}%") |
                StockMaster.name.ilike(f"{query}%")
            )
            .order_by(popularity.desc())
            .limit(num_suggestions)
            .all()
        )
        result = jsonify([{"ticker": match.ticker, "name": match.name} for match in matches])
    return result