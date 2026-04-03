from models.database import db, Index
from utils.db_queries.tables.dataset_version import get_active_dataset_id

def get_all_indices():
    dataset_version_id = get_active_dataset_id()

    all_indices = db.session.execute(
        db.select(Index)
        .where(Index.dataset_version_id == dataset_version_id)
    ).scalars().all()

    return all_indices