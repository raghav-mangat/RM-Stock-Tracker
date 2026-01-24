from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass
from models.database import (db, WatchlistFolder, WatchlistItem, WatchlistFolderAttribute,
                             WatchlistAlert, StockMaster, Stock, FolderAttribute, OrderBy)
from data_collectors.stock_data import fetch_stock_data

@dataclass
class MutationResult:
    ok: bool
    message: str
    status_code: int | None = None

class NotFoundError(Exception):
    pass

class ForbiddenError(Exception):
    pass

def db_get_all_watchlist_data(user):
    result = {}
    folders = get_all_user_folders(user)

    for folder in folders:
        result[folder.id] = db_get_folder_data(folder)
    return result

def db_get_folder_data(folder):
    folder_attributes_data = folder.folder_attributes
    folder_attributes_list = [folder_attribute.attribute for folder_attribute in folder.folder_attributes]

    folder_alerts = folder.alerts

    all_items_data = get_all_items_data(folder.id)

    # Filter the items data if filters are applied to the folder
    for attribute_data in folder_attributes_data:
        if attribute_data.attribute.value != FolderAttribute.NAME:
            use_abs = attribute_data.use_abs
            min_value = attribute_data.min_value
            max_value = attribute_data.max_value

            def all_items_data_filter(data):
                filter_result = False
                attribute_value = data[1]["stock_data"].get(attribute_data.attribute.value)
                if use_abs:
                    attribute_value = abs(attribute_value)

                if (min_value is not None) and (max_value is not None):
                    filter_result = min_value < attribute_value <= max_value
                elif min_value is not None:
                    filter_result = min_value < attribute_value
                elif max_value is not None:
                    filter_result = attribute_value <= max_value
                return filter_result

            if (min_value is not None) or (max_value is not None):
                all_items_data = dict(filter(
                    all_items_data_filter,
                    all_items_data.items()
                ))

    # Sort the items data if sorting is applied to the folder
    sort_by_attribute = folder.sort_by_attribute
    sort_by_order = folder.sort_by_order
    if sort_by_attribute and sort_by_order:
        reverse = (sort_by_order == OrderBy.DESC)
        all_items_data = dict(sorted(
            all_items_data.items(),
            key=lambda item: item[1]["stock_data"].get(sort_by_attribute, None),
            reverse=reverse
        ))

    result = {
        "folder_name": folder.name,
        "folder_order": folder.order,
        "folder_attributes_data": folder_attributes_data,
        "folder_attributes_list": folder_attributes_list,
        "folder_alerts": folder_alerts,
        "folder_items": all_items_data,
        "folder_sort_by_attribute": sort_by_attribute,
        "folder_sort_by_order": sort_by_order
    }

    return result

def db_get_num_folders(user):
    return len(user.watchlist_folders)

def db_add_folder(folder_name, user):
    try:
        folders = user.watchlist_folders
        order = len(folders) + 1
        new_folder = WatchlistFolder(name=folder_name, order=order, user=user)
        db.session.add(new_folder)
        db.session.flush()

        # Add default folder attributes
        add_default_folder_attributes(new_folder)

        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Folder '{folder_name}' added successfully.",
        )

    except IntegrityError:
        db.session.rollback()
        return MutationResult(
            ok=False,
            message=f"Folder '{folder_name}' already exists.",
            status_code=409,
        )
    except Exception as e:
        db.session.rollback()
        raise e

def db_rename_folder(new_folder_name, folder_id, user):
    try:
        folder = check_and_get_user_folder(folder_id, user)
        # Rename folder
        folder.name = new_folder_name
        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Folder renamed to '{new_folder_name}'.",
        )
    except IntegrityError:
        db.session.rollback()
        return MutationResult(
            ok=False,
            message=f"Folder '{new_folder_name}' already exists.",
            status_code=409,
        )
    except Exception as e:
        db.session.rollback()
        raise e

def db_remove_folder(folder_id, user):
    try:
        folder = check_and_get_user_folder(folder_id, user)
        folder_name = folder.name

        # Delete Folder
        db.session.delete(folder)
        db.session.flush()

        # Reorder all folders for the user after deletion
        folders = get_all_user_folders(user)
        for i in range(len(folders)):
            folders[i].order = i + 1

        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Folder '{folder_name}' removed successfully.",
        )
    except Exception as e:
        db.session.rollback()
        raise e

def db_update_order(folder_id, new_order, user):
    try:
        # The folder we need to update
        update_folder = check_and_get_user_folder(folder_id, user)

        # Get all the user's folders
        folders = get_all_user_folders(user)

        # Get the maximum order for user's folders
        max_order = len(folders)

        # Check if the new_order is valid
        if not 1 <= new_order <= max_order:
            raise Exception(f"New order '{new_order}' not in range ({1}, {max_order})")

        # Old order of the folder
        old_order = update_folder.order

        # Direction of shift for reordering of the folders
        if new_order < old_order:
            order_shift = 1
        else:
            order_shift = -1

        # Move target folder out of the way (temporary value)
        update_folder.order = max_order + 1
        db.session.flush()

        # Reorder the folders between new order and old order
        for i in range(new_order, old_order, order_shift):
            # Get the current folder
            curr_folder = folders[i-1]
            # Shift the folder
            curr_folder.order = curr_folder.order + order_shift
            db.session.flush()

        # Update the order of the given folder
        update_folder.order = new_order

        # Commit the reordering of the user's folders
        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Folder '{update_folder.name}' reordered successfully.",
        )

    except Exception as e:
        db.session.rollback()
        raise e

def db_add_watchlist_item(folder_id, stock, user):
    try:
        folder = check_and_get_user_folder(folder_id, user)

        watchlist_item = WatchlistItem(folder=folder, stock=stock)
        db.session.add(watchlist_item)
        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Added stock '{stock.ticker}'.",
        )

    except IntegrityError:
        db.session.rollback()
        return MutationResult(
            ok=False,
            message="This stock is already in the selected folder.",
            status_code=409,
        )
    except Exception as e:
        db.session.rollback()
        raise e

def db_remove_watchlist_item(item_id, user):
    try:
        item = check_and_get_user_item(item_id, user)
        ticker = item.stock.ticker
        folder_name = item.folder.name

        # Delete Watchlist item
        db.session.delete(item)
        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Removed stock '{ticker}' from folder '{folder_name}'.",
        )
    except Exception as e:
        db.session.rollback()
        raise e

def db_update_folder_alerts(folder_id, alerts, user):
    try:
        folder = check_and_get_user_folder(folder_id, user)

        delete_folder_alerts(folder, user)
        db.session.flush()

        for alert in alerts:
            if not alert["delete"]:
                db.session.add(
                    WatchlistAlert(
                        attribute=alert["attribute"],
                        use_abs=alert["use_abs"],
                        min_value=alert["min_value"],
                        max_value=alert["max_value"],
                        user=user,
                        folder=folder,
                    )
                )
        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Updated email alerts for folder '{folder.name}'.",
        )

    except Exception as e:
        db.session.rollback()
        raise e

def db_update_item_alerts(item_id, alerts, user):
    try:
        item = check_and_get_user_item(item_id, user)

        delete_item_alerts(item, user)
        db.session.flush()

        for alert in alerts:
            if not alert["delete"]:
                db.session.add(
                    WatchlistAlert(
                        attribute=alert["attribute"],
                        use_abs=alert["use_abs"],
                        min_value=alert["min_value"],
                        max_value=alert["max_value"],
                        user=user,
                        item=item,
                    )
                )

        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Updated email alerts for stock '{item.stock.ticker}' in folder '{item.folder.name}'.",
        )

    except Exception as e:
        db.session.rollback()
        raise e

def db_update_folder_attributes(folder_id, action, attributes, user):
    try:
        folder = check_and_get_user_folder(folder_id, user)

        for attribute in folder.folder_attributes:
            db.session.delete(attribute)
        db.session.flush()

        if action == "save":
            for attribute in attributes:
                db.session.add(WatchlistFolderAttribute(
                    attribute=attribute,
                    folder=folder
                ))
            db.session.flush()
        elif action == "restore":
            add_default_folder_attributes(folder)
        else:
            raise Exception(f"Form action '{action}' does not exist.")

        # Reset folder sorting
        folder.sort_by_attribute = None
        folder.sort_by_order = None
        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Updated attributes for folder '{folder.name}'.",
        )

    except Exception as e:
        db.session.rollback()
        raise e

def db_update_folder_sort_by(folder_id, sort_by_attribute, sort_by_order, user):
    try:
        folder = check_and_get_user_folder(folder_id, user)
        if folder.sort_by_attribute == sort_by_attribute and folder.sort_by_order == sort_by_order:
            folder.sort_by_attribute = None
            folder.sort_by_order = None
        else:
            folder.sort_by_attribute = sort_by_attribute
            folder.sort_by_order = sort_by_order
        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Updated sorting for folder '{folder.name}'.",
        )

    except Exception as e:
        db.session.rollback()
        raise e

def db_update_attribute_filters(attribute_id, use_abs, min_value, max_value, user):
    try:
        attribute = check_and_get_folder_attribute(attribute_id, user)
        attribute.use_abs = use_abs
        attribute.min_value = min_value
        attribute.max_value = max_value
        db.session.commit()

        return MutationResult(
            ok=True,
            message=f"Updated filters for folder '{attribute.folder.name}'.",
        )

    except Exception as e:
        db.session.rollback()
        raise e

def check_and_get_user_folder(folder_id, user):
    folder = get_folder_by_id(folder_id)
    if not folder:
        raise NotFoundError(f"Folder with id {folder_id} not found.")
    if folder.user_id != user.id:
        raise ForbiddenError(f"Folder with id {folder_id} does not belong to user with id {user.id}")
    return folder

def check_and_get_user_item(item_id, user):
    item = db.session.execute(db.select(WatchlistItem).where(WatchlistItem.id == item_id)).scalar()
    if not item:
        raise NotFoundError(f"Item with id {item_id} not found.")
    if item.folder.user_id != user.id:
        raise ForbiddenError(f"Item with id {item_id} does not belong to the user with id {user.id}")
    return item

def check_and_get_folder_attribute(attribute_id, user):
    attribute = db.session.execute(db.select(WatchlistFolderAttribute).where(WatchlistFolderAttribute.id == attribute_id)).scalar()
    folder = attribute.folder
    if not attribute:
        raise NotFoundError(f"Attribute with id {attribute_id} not found.")
    if folder and folder.user_id != user.id:
        raise ForbiddenError(f"Attribute with id {attribute_id} does not belong to user with id {user.id}")
    return attribute

def add_default_folder_attributes(folder):
    db.session.add(WatchlistFolderAttribute(
        attribute=FolderAttribute.NAME,
        folder=folder
    ))
    db.session.add(WatchlistFolderAttribute(
        attribute=FolderAttribute.DAY_CLOSE,
        folder=folder
    ))
    db.session.add(WatchlistFolderAttribute(
        attribute=FolderAttribute.TODAYS_CHANGE_PERC,
        folder=folder
    ))
    db.session.add(WatchlistFolderAttribute(
        attribute=FolderAttribute.DMA_200,
        folder=folder
    ))
    db.session.add(WatchlistFolderAttribute(
        attribute=FolderAttribute.DMA_200_PERC_DIFF,
        folder=folder
    ))
    db.session.add(WatchlistFolderAttribute(
        attribute=FolderAttribute.LOW_52W,
        folder=folder
    ))
    db.session.add(WatchlistFolderAttribute(
        attribute=FolderAttribute.HIGH_52W,
        folder=folder
    ))
    db.session.flush()

def delete_folder_alerts(folder, user):
    for alert in folder.alerts:
        if alert.user != user:
            raise ForbiddenError(f"Alert with id {alert.id} does not belong to the user with id {user.id}")
        db.session.delete(alert)
        db.session.flush()
    db.session.flush()

def delete_item_alerts(item, user):
    for alert in item.alerts:
        if alert.user != user:
            raise ForbiddenError(f"Alert with id {alert.id} does not belong to the user with id {user.id}")
        db.session.delete(alert)
        db.session.flush()
    db.session.flush()

def get_folder_by_id(folder_id):
    folder = db.session.execute(db.select(WatchlistFolder).where(WatchlistFolder.id == folder_id)).scalar()
    return folder

def get_item_by_id(item_id):
    item = db.session.execute(db.select(WatchlistItem).where(WatchlistItem.id == item_id)).scalar()
    return item

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

def get_folder_items(folder_id):
    result = db.session.query(
        StockMaster.ticker,
        WatchlistItem.id
    ).join(
        WatchlistItem
    ).join(
        WatchlistFolder
    ).where(
        WatchlistFolder.id == folder_id
    ).all()
    return result

def get_ticker_stock_data(ticker):
    # Check if the stock is present in the database
    stock_data = db.session.execute(
        db.select(
            Stock
        ).where(
            Stock.ticker == ticker
        )
    ).scalar()

    # If not in db then use stock data collector script to get stock data
    if not stock_data:
        stock_data = fetch_stock_data(ticker)

    # Return the stock_data
    return stock_data.to_dict()

def get_all_items_data(folder_id):
    folder_items = get_folder_items(folder_id)

    all_items_data = {}
    for ticker, item_id in folder_items:
        stock_data = get_ticker_stock_data(ticker)
        if stock_data:
            item = get_item_by_id(item_id)
            if item:
                all_items_data[item_id] = {
                    "stock_data": stock_data,
                    "item_alerts": item.alerts
                }

    return all_items_data

def stock_data_filter(stock_data, alerts):
    filter_result = False
    for alert in alerts:
        attribute = alert.attribute
        use_abs = alert.use_abs
        min_value = alert.min_value
        max_value = alert.max_value
        attribute_value = stock_data.get(attribute.value)

        if use_abs:
            attribute_value = abs(attribute_value)

        if (min_value is not None) and (max_value is not None):
            filter_result = min_value < attribute_value <= max_value
        elif min_value is not None:
            filter_result = min_value < attribute_value
        elif max_value is not None:
            filter_result = attribute_value <= max_value

        if not filter_result:
            return filter_result

    return filter_result

def db_get_watchlist_alert_data(user):
    """
    - Structure of the data returned by this function:

    watchlist_alert_data = [
        {
            "folder_id": None,
            "folder_order": None,
            "folder_name": None,
            "num_items": None,
            "folder_alerts": [
                {
                    "alert": None,
                    "stocks": [
                        "stock_data_1",
                        "stock_data_2"
                    ]
                }
            ],
            "all_folder_alerts": {
                "alerts": [],
                "stocks": []
            },
            "item_alerts": [
                {
                    "stock_data": None,
                    "num_triggered": None,
                    "num_non_triggered": None,
                    "alerts": [
                        {
                            "alert": None,
                            "triggered": None
                        },
                        {
                            "alert": None,
                            "triggered": None
                        }
                    ]
                }
            ]
        }
    ]
    """

    # List of data to return
    watchlist_alert_data = list()

    # All user's folders
    folders = get_all_user_folders(user)

    # For each folder
    for folder in folders:
        # Collect folder data
        folder_data = {
            "folder_id": folder.id,
            "folder_order": folder.order,
            "folder_name": folder.name
        }

        # Get data for each item in the folder
        all_items_data = get_all_items_data(folder.id)

        # Store the number of items in the folder
        folder_data["num_items"] = len(all_items_data.items())

        # Get all alerts for the folder
        folder_alerts = folder.alerts

        # For each alert in the folder
        folder_data["folder_alerts"] = []
        for alert in folder_alerts:
            # Get a list of all the stocks in the folder that match the alert
            filter_all_stock_data = [
                value.get("stock_data")
                for value in all_items_data.values()
                if stock_data_filter(
                    value.get("stock_data"),
                    [alert]
                )
            ]

            # Store the alert with the associated stocks
            folder_data["folder_alerts"].append({
                "alert": alert,
                "stocks": filter_all_stock_data
            })

        # Store all the folder's alerts as a list along with the list of
        # stocks in the folder that match all the alerts combined
        folder_data["all_folder_alerts"] = {
            "alerts": folder_alerts,
            "stocks": [
                value.get("stock_data")
                for value in all_items_data.values()
                if stock_data_filter(
                    value.get("stock_data"),
                    folder_alerts
                )
            ]
        }

        # For each item in the folder
        folder_data["item_alerts"] = []
        for value in all_items_data.values():
            # If the item has alerts
            if value.get("item_alerts"):
                # Get the stock data for the item
                stock_data = value.get("stock_data")

                # For each alert for the item
                item_alerts = []
                num_triggered = 0
                num_non_triggered = 0
                for item_alert in value.get("item_alerts"):
                    # Store the alert along with a boolean to tell if the
                    # stock matches the alert
                    alert = {
                        "alert": item_alert,
                        "triggered": False
                    }
                    if stock_data_filter(stock_data, [item_alert]):
                        alert["triggered"] = True
                        num_triggered += 1
                    else:
                        num_non_triggered += 1
                    item_alerts.append(alert)

                # Store this data for the item
                folder_data["item_alerts"].append({
                    "stock_data": stock_data,
                    "num_triggered": num_triggered,
                    "num_non_triggered": num_non_triggered,
                    "alerts": item_alerts
                })

        # Store all of this data for the folder
        watchlist_alert_data.append(folder_data)

    # Return the data for all the folders
    return watchlist_alert_data

def db_get_watchlist_alert_email_data(user):
    # Maximum number of folders for which we include the data in the email
    max_num_folders = 10

    # Get watchlist alert data for the user
    watchlist_alert_data = db_get_watchlist_alert_data(user)

    # Extracted email data to return
    email_data = []

    # For each folder in the user's watchlist
    for folder in watchlist_alert_data:
        # If we have reached the limit, stop collecting data
        if len(email_data) >= max_num_folders:
            break

        # Get the required data
        item_alerts = folder.get("item_alerts", [])
        folder_alerts = folder.get("folder_alerts", [])
        all_folder_alerts = folder.get("all_folder_alerts", {})

        # If the folder has any alerts, then include the data for that folder
        if folder_alerts or item_alerts:
            # Number of stocks in the folder that have at least one alert triggered
            stocks_with_triggered_item_alerts = 0
            for item in item_alerts:
                if any(alert["triggered"] for alert in item.get("alerts", [])):
                    stocks_with_triggered_item_alerts += 1

            # Store the data for the folder
            email_data.append({
                # Folder data
                "folder_order": folder["folder_order"],
                "folder_name": folder["folder_name"],

                # Folder-level alerts
                "folder_alert_count": len(folder_alerts),
                "stocks_matching_all_folder_alerts": len(
                    all_folder_alerts.get("stocks", [])
                ),

                # Item-level alerts
                "stocks_with_item_alerts": len(item_alerts),
                "stocks_with_triggered_item_alerts": stocks_with_triggered_item_alerts,
            })

    return email_data
