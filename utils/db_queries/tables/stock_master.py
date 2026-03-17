from sqlalchemy.orm import joinedload
from models.database import db, StockMaster

def get_all_stock_master_by_dataset_version(dataset_version_id):
    return (
        db.session.query(StockMaster)
        .options(joinedload(StockMaster.ticker))
        .where(StockMaster.dataset_version_id == dataset_version_id)
        .all()
    )