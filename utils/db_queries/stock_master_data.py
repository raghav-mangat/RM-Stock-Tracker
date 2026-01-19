from models.database import db, StockMaster

def get_stock_master_by_ticker(ticker):
    stock = db.session.execute(db.select(StockMaster).where(StockMaster.ticker == ticker)).scalar()
    return stock

def get_all_stock_master():
    return db.session.execute(db.select(StockMaster)).scalars().all()