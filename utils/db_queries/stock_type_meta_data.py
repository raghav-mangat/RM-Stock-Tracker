from models.database import db, StockTypeMeta

def get_stock_type_by_code(code):
    stock_type = db.session.execute(db.select(StockTypeMeta).where(StockTypeMeta.code == code)).scalar()
    return stock_type

def get_all_stock_types():
    return db.session.execute(db.select(StockTypeMeta)).scalars().all()