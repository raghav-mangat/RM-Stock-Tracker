from models.database import db, DatasetVersion

def get_active_dataset_id():
    return db.session.execute(
        db.select(DatasetVersion.id)
        .where(DatasetVersion.is_active == True)
    ).scalar()

def get_active_dataset_market_status():
    return db.session.execute(
        db.select(DatasetVersion.market_status)
        .where(DatasetVersion.is_active == True)
    ).scalar()