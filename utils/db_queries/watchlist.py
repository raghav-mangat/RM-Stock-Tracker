from models.database import db, WatchlistFolder, WatchlistItem, StockMaster, Stock
from data_collectors.stock_data import fetch_stock_data

def get_all_watchlist_data(user):
    result = {}
    folders = db.session.execute(
        db.select(
            WatchlistFolder
        ).where(
            WatchlistFolder.user == user
        )
    ).scalars().all()

    for folder in folders:
        stocks = db.session.execute(
            db.select(
                StockMaster
            ).join(
                WatchlistItem
            ).join(
                WatchlistFolder
            ).where(
                WatchlistFolder.id == folder.id
            )
        ).scalars().all()

        all_stock_data = []
        for stock in stocks:
            ticker = stock.ticker
            # Check if the stock is present in the database
            stock_data = Stock.query.filter_by(ticker=ticker).first()
            # if not in db then use stock data collector script to get stock data
            if not stock_data:
                stock_data = fetch_stock_data(ticker)
            if stock_data:
                all_stock_data.append(stock_data)
        result[folder.id] = {
            "folder_name": folder.name,
            "folder_items": all_stock_data
        }
    return result

def db_add_folder(folder_name, user):
    result = True
    folders = user.watchlist_folders
    for folder in folders:
        if folder.name == folder_name:
            result = False

    if result:
        new_folder = WatchlistFolder(name=folder_name, user=user)
        db.session.add(new_folder)
        db.session.commit()
    return result

def db_rename_folder(folder_id, new_folder_name):
    rename_folder = True
    existing_folder = db.session.execute(db.select(WatchlistFolder).where(WatchlistFolder.name == new_folder_name)).scalar()
    if existing_folder:
        rename_folder = False
    else:
        folder = db.session.execute(db.select(WatchlistFolder).where(WatchlistFolder.id==folder_id)).scalar()
        folder.name = new_folder_name
        db.session.commit()
    return rename_folder

def db_delete_folder(folder_id):
    folder = db.session.execute(db.select(WatchlistFolder).where(WatchlistFolder.id == folder_id)).scalar()
    db.session.delete(folder)
    db.session.commit()

def get_folder_by_id(folder_id):
    folder = db.session.execute(db.select(WatchlistFolder).where(WatchlistFolder.id == folder_id)).scalar()
    return folder

def get_stock_master_by_ticker(ticker):
    stock = db.session.execute(db.select(StockMaster).where(StockMaster.ticker == ticker)).scalar()
    return stock

def get_watchlist_item(folder, stock):
    watchlist_item = db.session.execute(db.select(WatchlistItem).where(WatchlistItem.folder_id==folder.id, WatchlistItem.stock_id==stock.id)).scalar()
    return watchlist_item

def add_watchlist_item(folder, stock):
    watchlist_item = WatchlistItem(folder=folder, stock=stock)
    db.session.add(watchlist_item)
    db.session.commit()

def remove_watchlist_item(folder_id, ticker):
    stock_id = db.session.execute(db.select(StockMaster.id).where(StockMaster.ticker == ticker)).scalar()
    watchlist_item = db.session.execute(db.select(WatchlistItem).where(folder_id==folder_id, stock_id==stock_id)).scalar()
    db.session.delete(watchlist_item)
    db.session.commit()