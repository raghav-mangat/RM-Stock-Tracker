from . import watchlist_bp
from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from utils.populate_db_info import db_last_updated
from utils.db_queries.watchlist import *

@watchlist_bp.route('/', methods=["GET"])
def index():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    if current_user.is_authenticated:
        watchlist_data = db_get_all_watchlist_data(current_user)
        return render_template("watchlist_loggedin.html", watchlist_data=watchlist_data, last_updated=last_updated)
    else:
        return render_template("watchlist_loggedout.html", last_updated=last_updated)

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

@watchlist_bp.route("/delete_folder/<int:folder_id>", methods=["POST"])
@login_required
def delete_folder(folder_id):
    try:
        db_delete_folder(folder_id=folder_id, user=current_user)
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
        flash("Not authorized to remove stock from this folder", "danger")
    except Exception:
        flash("An error occurred while removing stock from this folder.", "danger")
    else:
        flash(f"Removed stock '{ticker}'.", "success")
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
    elif db_check_duplicate_folder(folder_name, current_user):
        result["message"] = f"Folder '{folder_name}' already exists."
    else:
        result["valid"] = True
        result["folder_name"] = folder_name

    return result