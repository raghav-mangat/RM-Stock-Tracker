from . import watchlist_bp
from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from models.database import AlertAttribute
from utils.populate_db_info import db_last_updated
from utils.db_queries.watchlist import *

@watchlist_bp.route('/', methods=["GET"])
def index():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    if not current_user.is_authenticated:
        return render_template("watchlist_loggedout.html", last_updated=last_updated)

    watchlist_data = db_get_all_watchlist_data(current_user)

    return render_template(
        "watchlist_loggedin.html",
        watchlist_data=watchlist_data,
        FolderAttribute=FolderAttribute,
        AlertAttribute=AlertAttribute,
        OrderBy=OrderBy,
        last_updated=last_updated
    )

@watchlist_bp.route("/add_folder", methods=["POST"])
@login_required
def add_folder():
    # Redirect to 'next' if provided, else fallback
    url = url_for("watchlist.index")
    next_url = request.form.get("next")
    if next_url:
        url = next_url

    folder_name = request.form.get("folder_name")
    folder_name_result = validate_folder_name(folder_name)
    if folder_name_result["valid"]:
        try:
            db_add_folder(folder_name_result["folder_name"], current_user)
        except Exception:
            flash("An error occurred while adding the folder.", "danger")
        else:
            flash(f"Folder '{folder_name_result["folder_name"]}' added successfully.", "success")
    else:
        flash(folder_name_result["message"], "warning")

    return redirect(url)

@watchlist_bp.route("/rename_folder/<int:folder_id>", methods=["POST"])
@login_required
def rename_folder(folder_id):
    new_folder_name = request.form.get("new_folder_name")
    folder_name_result = validate_folder_name(new_folder_name)
    if folder_name_result["valid"]:
        try:
            db_rename_folder(folder_name_result["folder_name"], folder_id, current_user)
        except NotFoundError:
            flash("Folder not found.", "danger")
        except ForbiddenError:
            flash("Not authorized to rename this folder.", "danger")
        except Exception:
            flash("An error occurred while renaming the folder.", "danger")
        else:
            flash(f"Folder renamed to '{folder_name_result["folder_name"]}'.", "success")
    else:
        flash(folder_name_result["message"], "warning")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/remove_folder/<int:folder_id>", methods=["POST"])
@login_required
def remove_folder(folder_id):
    try:
        db_remove_folder(folder_id=folder_id, user=current_user)
    except NotFoundError:
        flash("Folder not found.", "danger")
    except ForbiddenError:
        flash("Not authorized to delete this folder", "danger")
    except Exception:
        flash("An error occurred while deleting the folder.", "danger")
    else:
        flash("Folder deleted successfully.", "success")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/update_order/<int:folder_id>", methods=["POST"])
@login_required
def update_order(folder_id):
    new_order = int(request.form.get("order"))
    try:
        db_update_order(folder_id, new_order, current_user)
    except NotFoundError:
        flash("Folder not found.", "danger")
    except ForbiddenError:
        flash("Not authorized to reorder this folder", "danger")
    except Exception:
        flash("An error occurred while reordering the folder.", "danger")
    else:
        flash("Folder reordered successfully!", "success")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/add-item/", methods=["POST"])
@login_required
def add_item():
    # Redirect to 'next' if provided, else fallback
    url = url_for("watchlist.index")
    next_url = request.form.get("next")
    if next_url:
        url = next_url

    ticker = request.form.get("ticker")
    stock = get_stock_master_by_ticker(ticker)
    if stock:
        folder_id = request.form.get("folder_id")
        try:
            db_add_watchlist_item(folder_id=folder_id, stock=stock, user=current_user)
        except NotFoundError:
            flash("Folder not found.", "danger")
        except ForbiddenError:
            flash("Not authorized to add stock to this folder", "danger")
        except DuplicateError:
            flash("This stock is already in the selected folder.", "warning")
        except Exception:
            flash("An error occurred while adding stock to this folder.", "danger")
        else:
            flash(f"Added stock '{ticker}'.", "success")
    else:
        flash(f"Please search for a valid stock.", "warning")
    return redirect(url)

@watchlist_bp.route("/remove_item/<int:folder_id>/<string:ticker>", methods=["POST"])
@login_required
def remove_item(folder_id, ticker):
    try:
        db_remove_watchlist_item(folder_id=folder_id, ticker=ticker, user=current_user)
    except NotFoundError:
        flash("Folder or stock not found.", "danger")
    except ForbiddenError:
        flash("Not authorized to remove stock from this folder.", "danger")
    except Exception:
        flash("An error occurred while removing stock from this folder.", "danger")
    else:
        flash(f"Removed stock '{ticker}'.", "success")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/update_folder_alerts/<int:folder_id>", methods=["POST"])
def update_folder_alerts(folder_id):
    folder_name = request.form.get("folder_name")

    alerts = get_alerts(request)
    message = validate_alerts(alerts)

    if message:
        flash(message, "warning")
    else:
        try:
            db_update_folder_alerts(folder_id, alerts, current_user)
        except NotFoundError:
            flash("Folder not found.", "danger")
        except ForbiddenError:
            flash("Not authorized to update alerts for this folder.", "danger")
        except Exception:
            flash("An error occurred while updating the alerts for this folder.", "danger")
        else:
            flash(f"Updated email alerts for folder '{folder_name}'.", "success")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/update_item_alerts/<int:item_id>", methods=["POST"])
def update_item_alerts(item_id):
    ticker = request.form.get("ticker")
    folder_name = request.form.get("folder_name")

    alerts = get_alerts(request)
    message = validate_alerts(alerts)

    if message:
        flash(message, "warning")
    else:
        try:
            db_update_item_alerts(item_id, alerts, current_user)
        except NotFoundError:
            flash("Stock not found.", "danger")
        except ForbiddenError:
            flash("Not authorized to update alerts for this stock.", "danger")
        except Exception:
            flash("An error occurred while updating the alerts for this stock.", "danger")
        else:
            flash(f"Updated email alerts for stock '{ticker}' in folder '{folder_name}'.", "success")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/update_folder_attributes/<int:folder_id>", methods=["POST"])
def update_folder_attributes(folder_id):
    folder_name = request.form.get("folder_name")
    action = request.form.get("action")
    selected_attributes = []

    if action == "save":
        all_folder_attributes = list(FolderAttribute)
        for i in range(1, len(all_folder_attributes) + 1):
            attribute = request.form.get(f"folder-attribute-{i}")
            if attribute:
                if attribute in all_folder_attributes:
                    selected_attributes.append(attribute)
                else:
                    flash(f"Invalid folder attribute selected.", "danger")
                    return redirect(url_for("watchlist.index"))

        min_selections = 2
        max_selections = 8
        if len(selected_attributes) < min_selections:
            flash(f"Select at least {min_selections} attributes", "warning")
            return redirect(url_for("watchlist.index"))
        if len(selected_attributes) > max_selections:
            flash(f"Cannot select more than {max_selections} attributes", "warning")
            return redirect(url_for("watchlist.index"))

    try:
        db_update_folder_attributes(folder_id, action, selected_attributes, current_user)
    except NotFoundError:
        flash("Folder not found.", "danger")
    except ForbiddenError:
        flash("Not authorized to update attributes for this folder.", "danger")
    except Exception:
        flash("An error occurred while updating the attributes for this folder.", "danger")
    else:
        flash(f"Updated attributes for folder '{folder_name}'.", "success")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/update_folder_sort_by/<int:folder_id>", methods=["POST"])
def update_folder_sort_by(folder_id):
    sort_by_attribute = request.form.get("sort_by_attribute")
    sort_by_order = request.form.get("sort_by_order")

    if (sort_by_attribute in list(FolderAttribute)) and (sort_by_order in list(OrderBy)):
        try:
            db_update_folder_sort_by(folder_id, sort_by_attribute, sort_by_order, current_user)
        except NotFoundError:
            flash("Folder not found.", "danger")
        except ForbiddenError:
            flash("Not authorized to update sorting for this folder.", "danger")
        except Exception:
            flash("An error occurred while updating the sorting for this folder.", "danger")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/update_attribute_filters/<int:attribute_id>", methods=["POST"])
def update_attribute_filters(attribute_id):
    action = request.form.get("action")
    if action not in ["apply", "clear"]:
        return redirect(url_for("watchlist.index"))

    (min_value, max_value, message) = (None, None, None)

    if action == "apply":
        min_value = request.form.get("min-value")
        max_value = request.form.get("max-value")

        (min_value, max_value, message) = validate_values(min_value, max_value)

    if message:
        flash(message, "warning")
    else:
        try:
            db_update_attribute_filters(attribute_id, min_value, max_value, current_user)
        except NotFoundError:
            flash("Attribute not found.", "danger")
        except ForbiddenError:
            flash("Not authorized to update filters for this attribute.", "danger")
        except Exception:
            flash("An error occurred while updating the filters for this attribute.", "danger")
    return redirect(url_for("watchlist.index"))

def validate_folder_name(folder_name):
    max_folder_name_len = 50
    result = {
        "valid": False,
        "message": "",
        "folder_name": ""
    }
    if not folder_name:
        result["message"] = "Folder name cannot be empty."
        return result

    folder_name = folder_name.strip().upper()
    if len(folder_name) > max_folder_name_len:
        result["message"] = f"Folder name must be at most {max_folder_name_len} characters."
    elif check_duplicate_folder(folder_name, current_user):
        result["message"] = f"Folder '{folder_name}' already exists."
    else:
        result["valid"] = True
        result["folder_name"] = folder_name

    return result

def get_alerts(update_alert_request):
    num_alerts = int(update_alert_request.form.get("num_alerts"))

    # Get values for all form inputs, save as dict for each alert
    alerts = []
    for i in range(1, num_alerts + 1):
        alerts.append({
            "attribute": update_alert_request.form.get(f"attribute-{i}"),
            "min_value": update_alert_request.form.get(f"min-value-{i}"),
            "max_value": update_alert_request.form.get(f"max-value-{i}"),
            "delete": update_alert_request.form.get(f"delete-{i}")
        })
    new_alert = {
        "attribute": update_alert_request.form.get("attribute-new"),
        "min_value": update_alert_request.form.get(f"min-value-new"),
        "max_value": update_alert_request.form.get(f"max-value-new"),
        "delete": None
    }
    # Add the new alert only if there was a selection made in it
    if new_alert["attribute"] or new_alert["min_value"] or new_alert["max_value"]:
        alerts.append(new_alert)

    return alerts

def validate_alerts(alerts):
    # Check if the user input is valid for all alerts
    message = None

    # To keep track of attributes selected by the user
    selected_attributes = set()

    for alert in alerts:
        if not alert["delete"]:
            attribute = alert["attribute"]
            if not attribute:
                message = "Please select an attribute."
                break
            if attribute not in list(AlertAttribute):
                message = "Invalid attribute selected."
                break
            if attribute in selected_attributes:
                message = f"Duplicate alert for '{attribute}'. Each attribute can have only one alert."
                break
            selected_attributes.add(attribute)

            (min_value, max_value, message) = validate_values(alert["min_value"], alert["max_value"])

            if message:
                break
            else:
                alert["min_value"] = min_value
                alert["max_value"] = max_value

    return message

def validate_values(min_value, max_value):
    message = None
    min_value_allowed = -1_000_000
    max_value_allowed = 1_000_000

    if not min_value and not max_value:
        min_value = None
        max_value = None
        message = "Please enter a value."
    else:
        try:
            if min_value:
                min_value = round(float(min_value), 2)
                if min_value < min_value_allowed:
                    message = f"Minimum value allowed is {min_value_allowed:,}"
                elif min_value > max_value_allowed:
                    message = f"Maximum value allowed is {max_value_allowed:,}"
            else:
                min_value = None
            if max_value:
                max_value = round(float(max_value), 2)
                if max_value < min_value_allowed:
                    message = f"Minimum value allowed is {min_value_allowed:,}"
                elif max_value > max_value_allowed:
                    message = f"Maximum value allowed is {max_value_allowed:,}"
            else:
                max_value = None

            if not message and (min_value is not None) and (max_value is not None) and (min_value > max_value):
                message = f"Minimum value cannot be greater than maximum value."

        except ValueError:
            min_value = None
            max_value = None
            message = "Value must be a valid number."
    return min_value, max_value, message