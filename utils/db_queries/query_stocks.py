from flask import jsonify
import random
from models.database import db, StockMaster, TickerMaster, StockDetail
from utils.constants import NUM_SUGGESTIONS
from utils.db_queries.tables.dataset_version import get_active_dataset_id

def get_query_stocks(user_query, dataset_version_id=None):
    if not dataset_version_id:
        dataset_version_id = get_active_dataset_id()

    db_base_query = (
        db.session.query(
            TickerMaster.symbol.label("ticker"),
            StockDetail.name.label("name"),
        )
        .select_from(TickerMaster)
        .join(StockMaster, TickerMaster.id == StockMaster.ticker_id)
        .join(StockDetail, TickerMaster.id == StockDetail.ticker_id)
        .filter(
            TickerMaster.is_active == True,
            StockMaster.dataset_version_id == dataset_version_id
        )
        .order_by(StockMaster.popularity.desc())
    )

    if user_query:
        user_query_upper = user_query.upper()

        matches = (
            db_base_query
            .filter(
                TickerMaster.symbol.like(f"{user_query_upper}%") |
                StockDetail.name.ilike(f"{user_query}%")
            )
            .limit(NUM_SUGGESTIONS)
            .all()
        )

    else:
        matches = db_base_query.limit(NUM_SUGGESTIONS).all()
        random.shuffle(matches)

    return jsonify([
        {"ticker": m.ticker, "name": m.name}
        for m in matches
    ])