from models.database import db, Index

def get_all_indices():
    all_indices = db.session.execute(db.select(Index)).scalars().all()
    return all_indices