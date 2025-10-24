from models.database import (db, WatchlistFolder, WatchlistItem, WatchlistAlert,
                             WatchlistFolderAlert, WatchlistItemAlert, StockMaster,
                             Stock, AlertAttribute, AlertOperator)

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
        folder_alerts = db.session.execute(
            db.select(
                WatchlistAlert
            ).join(
                WatchlistFolderAlert
            ).where(
                WatchlistFolderAlert.folder_id == folder.id
            )
        ).scalars().all()

        items = db.session.query(
            StockMaster.ticker,
            WatchlistItem.id
        ).join(
            WatchlistItem
        ).join(
            WatchlistFolder
        ).where(
            WatchlistFolder.id == folder.id
        )

        all_items_data = {}
        for ticker, item_id in items:
            # Check if the stock is present in the database
            stock_data = Stock.query.filter_by(ticker=ticker).first()
            # if not in db then use stock data collector script to get stock data
            if not stock_data:
                stock_data = fetch_stock_data(ticker)
            if stock_data:
                item_alerts = db.session.execute(
                    db.select(
                        WatchlistAlert
                    ).join(
                        WatchlistItemAlert
                    ).where(
                        WatchlistItemAlert.item_id == item_id
                    )
                ).scalars().all()
                all_items_data[item_id] = {
                    "stock_data": stock_data,
                    "item_alerts": item_alerts
                }

        result[folder.id] = {
            "folder_name": folder.name,
            "folder_order": folder.order,
            "folder_alerts": folder_alerts,
            "folder_items": all_items_data
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

def db_remove_folder(folder_id, user):
    folder = get_user_folder_or_404(folder_id, user)

    # Delete the alerts for the folder
    delete_folder_alerts(folder, user)

    # Delete all the items in the folder
    for item in folder.items:
        delete_watchlist_item(item, user)

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
    # Check if stock exists
    stock_id = db.session.execute(
        db.select(StockMaster.id).where(
            StockMaster.ticker == ticker)
    ).scalar()
    if not stock_id:
        raise NotFoundError(f"Stock with id {stock_id} not found.")

    # Check if watchlist item exists
    watchlist_item = db.session.execute(
        db.select(WatchlistItem).where(
            WatchlistItem.folder_id==folder_id, WatchlistItem.stock_id==stock_id
        )
    ).scalar()
    if not watchlist_item:
        folder = get_user_folder_or_404(folder_id, user)
        if folder:
            raise NotFoundError(f"Folder with id {folder_id} does not have stock with id {stock_id}")

    delete_watchlist_item(watchlist_item, user)

def db_update_folder_alerts(folder_id, alerts, user):
    folder = get_user_folder_or_404(folder_id, user)

    delete_folder_alerts(folder, user)

    for alert in alerts:
        if not alert["delete"]:
            new_alert = WatchlistAlert(
                attribute=alert["attribute"],
                operator=alert["operator"],
                value=alert["value"],
                user=user
            )
            db.session.add(new_alert)
            db.session.flush()
            db.session.add(WatchlistFolderAlert(
                folder=folder,
                alert=new_alert
            ))
        db.session.flush()
    db.session.commit()

def db_update_item_alerts(item_id, alerts, user):
    item = get_user_item_or_404(item_id, user)

    delete_item_alerts(item, user)

    for alert in alerts:
        if not alert["delete"]:
            new_alert = WatchlistAlert(
                attribute=alert["attribute"],
                operator=alert["operator"],
                value=alert["value"],
                user=user
            )
            db.session.add(new_alert)
            db.session.flush()
            db.session.add(WatchlistItemAlert(
                item=item,
                alert=new_alert
            ))
        db.session.flush()
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

def get_user_folder_or_404(folder_id, user):
    folder = get_folder_by_id(folder_id)
    if not folder:
        raise NotFoundError(f"Folder with id {folder_id} not found.")
    if folder.user_id != user.id:
        raise ForbiddenError(f"Folder with id {folder_id} does not belong to user with id {user.id}")
    return folder

def get_user_item_or_404(item_id, user):
    item = db.session.execute(db.select(WatchlistItem).where(WatchlistItem.id == item_id)).scalar()
    if not item:
        raise NotFoundError(f"Item with id {item_id} not found.")
    if item.folder.user_id != user.id:
        raise ForbiddenError(f"Item with id {item_id} does not belong to the user with id {user.id}")
    return item

def delete_watchlist_item(item, user):
    # Delete the alerts for the item
    delete_item_alerts(item, user)

    # Delete Watchlist item
    db.session.delete(item)
    db.session.commit()

def delete_folder_alerts(folder, user):
    folder_alerts = db.session.execute(
        db.select(
            WatchlistAlert
        ).join(
            WatchlistFolderAlert
        ).where(
            WatchlistFolderAlert.folder_id == folder.id
        )
    ).scalars().all()

    for alert in folder_alerts:
        if alert.user != user:
            raise ForbiddenError(f"Alert with id {alert.id} does not belong to the user with id {user.id}")
        db.session.delete(alert)
        db.session.flush()
    db.session.commit()

def delete_item_alerts(item, user):
    item_alerts = db.session.execute(
        db.select(
            WatchlistAlert
        ).join(
            WatchlistItemAlert
        ).where(
            WatchlistItemAlert.item_id == item.id
        )
    ).scalars().all()

    for alert in item_alerts:
        if alert.user != user:
            raise ForbiddenError(f"Alert with id {alert.id} does not belong to the user with id {user.id}")
        db.session.delete(alert)
        db.session.flush()
    db.session.commit()

def check_duplicate_folder(folder_name, user):
    exists = db.session.execute(
        db.select(WatchlistFolder).where(
            WatchlistFolder.user_id == user.id,
            WatchlistFolder.name == folder_name
        )
    ).first()
    return bool(exists)

def get_alert_attributes():
    return {member.value: member.label for member in AlertAttribute}

def get_alert_operators():
    return [member.value for member in AlertOperator]
