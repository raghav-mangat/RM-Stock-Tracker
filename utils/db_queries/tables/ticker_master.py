from models.database import db, StockMaster, TickerMaster, StockDetail
from utils.db_queries.tables.dataset_version import get_active_dataset_id

def get_valid_ticker_master_by_ticker(ticker):
    active_dataset_id = get_active_dataset_id()
    return (
        db.session.query(TickerMaster)
        .join(StockMaster, TickerMaster.id == StockMaster.ticker_id)
        .join(StockDetail, TickerMaster.id == StockDetail.ticker_id)
        .filter(
            TickerMaster.is_active == True,
            TickerMaster.symbol == ticker,
            StockMaster.dataset_version_id == active_dataset_id
        )
        .scalar()
    )

def get_all_active_ticker_master():
    return (
        db.session.execute(
            db.select(TickerMaster).where(TickerMaster.is_active == True)
        ).scalars().all()
    )