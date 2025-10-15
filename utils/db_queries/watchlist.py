from models.database import db, WatchlistFolder, WatchlistItem, StockMaster, Stock
from data_collectors.stock_data import fetch_stock_data

class NotFoundError(Exception):
    pass

class ForbiddenError(Exception):
    pass

class DuplicateError(Exception):
    pass

def db_get_all_watchlist_data(user):
    result = {}
    folders = get_all_user_folders(user)

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
            "folder_order": folder.order,
            "folder_items": all_stock_data
        }
    return result

def db_add_folder(folder_name, user):
    folders = user.watchlist_folders
    order = len(folders) + 1
    new_folder = WatchlistFolder(name=folder_name, order=order, user=user)
    db.session.add(new_folder)
    db.session.commit()

def db_rename_folder(new_folder_name, folder_id, user):
    folder = get_user_folder_or_404(folder_id, user)
    # Rename folder
    folder.name = new_folder_name
    db.session.commit()

def db_delete_folder(folder_id, user):
    folder = get_user_folder_or_404(folder_id, user)

    # Delete Folder
    db.session.delete(folder)
    db.session.flush()

    # Reorder all folders for the user after deletion
    folders = get_all_user_folders(user)
    for i in range(len(folders)):
        folders[i].order = i + 1

    db.session.commit()

def db_update_order(folder_id, new_order, user):
    # The folder we need to update
    update_folder = get_user_folder_or_404(folder_id, user)

    # Get all the user's folders
    folders = get_all_user_folders(user)

    # Old order of the folder
    old_order = update_folder.order

    # Direction of shift for reordering of the folders
    if new_order < old_order:
        order_shift = 1
    else:
        order_shift = -1

    # Reorder the folders between new order and old order
    for i in range(new_order, old_order, order_shift):
        # Get the current folder
        curr_folder = folders[i-1]
        # Shift the folder
        curr_folder.order = curr_folder.order + order_shift
    # Update the order of the given folder
    update_folder.order = new_order

    # Commit the reordering of the user's folders
    db.session.commit()

def db_add_watchlist_item(folder_id, stock, user):
    folder = get_user_folder_or_404(folder_id, user)

    existing_watchlist_item = get_watchlist_item(folder=folder, stock=stock)
    if existing_watchlist_item:
        raise DuplicateError(f"The ticker {stock.ticker} is already in the folder with id {folder.id}.")

    watchlist_item = WatchlistItem(folder=folder, stock=stock)
    db.session.add(watchlist_item)
    db.session.commit()

def db_remove_watchlist_item(folder_id, ticker, user):
    stock_id = db.session.execute(
        db.select(StockMaster.id).where(
            StockMaster.ticker == ticker)
    ).scalar()
    if not stock_id:
        raise NotFoundError(f"Stock with id {stock_id} not found.")
    watchlist_item = db.session.execute(
        db.select(WatchlistItem).where(
            WatchlistItem.folder_id==folder_id, WatchlistItem.stock_id==stock_id
        )
    ).scalar()
    if not watchlist_item:
        folder = get_user_folder_or_404(folder_id, user)
        if folder:
            raise NotFoundError(f"Folder with id {folder_id} does not have stock with id {stock_id}")

    db.session.delete(watchlist_item)
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

def get_all_user_folders(user):
    """
    Helper function that returns a list of all folders for the given user,
    in ascending order of the 'order'.
    """
    folders = db.session.execute(
        db.select(
            WatchlistFolder
        ).where(
            WatchlistFolder.user == user
        ).order_by(
            WatchlistFolder.order.asc()
        )
    ).scalars().all()
    return folders

def db_check_duplicate_folder(folder_name, user):
    exists = db.session.execute(
        db.select(WatchlistFolder).where(
            WatchlistFolder.user_id == user.id,
            WatchlistFolder.name == folder_name
        )
    ).first()
    return bool(exists)

def get_user_folder_or_404(folder_id, user):
    folder = get_folder_by_id(folder_id)
    if not folder:
        raise NotFoundError(f"Folder with id {folder_id} not found.")
    if folder.user_id != user.id:
        raise ForbiddenError(f"Folder with id {folder_id} does not belong to user with id {user.id}")
    return folder