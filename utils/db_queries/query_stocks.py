from flask import jsonify
import random
from models.database import db, StockSearch
from utils.constants import NUM_SUGGESTIONS
from utils.db_queries.tables.dataset_version import get_active_dataset_id

def get_query_stocks(user_query, dataset_version_id=None):
    if not dataset_version_id:
        dataset_version_id = get_active_dataset_id()

    if user_query:
        user_query = user_query.strip()

        symbol_query = user_query.upper()
        name_query = user_query.lower()

        matches = (
            db.session.query(
                StockSearch.symbol.label("ticker"),
                StockSearch.name.label("name"),
            )
            .filter(
                StockSearch.dataset_version_id == dataset_version_id,
                (
                    StockSearch.symbol.like(f"{symbol_query}%") |
                    StockSearch.name_lower.like(f"{name_query}%")
                )
            )
            .order_by(StockSearch.popularity.desc())
            .limit(NUM_SUGGESTIONS)
            .all()
        )

    else:
        matches = (
            db.session.query(
                StockSearch.symbol.label("ticker"),
                StockSearch.name.label("name"),
            )
            .filter(
                StockSearch.dataset_version_id == dataset_version_id,
            )
            .order_by(StockSearch.popularity.desc())
            .limit(NUM_SUGGESTIONS)
            .all()
        )

        random.shuffle(matches)

    return jsonify([
        {"ticker": m.ticker, "name": m.name}
        for m in matches
    ])