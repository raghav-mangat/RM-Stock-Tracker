from . import watchlist_bp
from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from utils.populate_db_info import db_last_updated
from utils.db_queries.watchlist import get_all_watchlist_data, db_add_folder, db_rename_folder, db_delete_folder, get_folder_by_id, get_stock_master_by_ticker, get_watchlist_item, add_watchlist_item, remove_watchlist_item

@watchlist_bp.route('/', methods=["GET"])
def index():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    if current_user.is_authenticated:
        watchlist_data = get_all_watchlist_data(current_user)
        return render_template("watchlist_loggedin.html", watchlist_data=watchlist_data, last_updated=last_updated)
    else:
        return render_template("watchlist_loggedout.html", last_updated=last_updated)

@watchlist_bp.route("/add_folder", methods=["POST"])
@login_required
def add_folder():
    folder_name = request.form.get("folder_name")
    if not folder_name:
        flash("Folder name cannot be empty", "danger")
        return redirect(url_for("watchlist.index"))

    folder_name = folder_name.strip().upper()
    if db_add_folder(folder_name=folder_name, user=current_user):
        flash(f"Folder '{folder_name}' added successfully!", "success")
    else:
        flash(f"Folder '{folder_name}' already exists.", "warning")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/rename_folder/<int:folder_id>", methods=["POST"])
@login_required
def rename_folder(folder_id):
    new_folder_name = request.form.get("new_folder_name")
    if not new_folder_name:
        flash("Folder name cannot be empty!", "danger")
        return redirect(url_for("watchlist.index"))

    if db_rename_folder(folder_id, new_folder_name):
        flash(f"Folder renamed to {new_folder_name}!", "success")
    else:
        flash("Cannot have duplicate folders!", "warning")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/delete_folder/<int:folder_id>", methods=["POST"])
@login_required
def delete_folder(folder_id):
    db_delete_folder(folder_id)
    flash("Folder deleted successfully!", "success")
    return redirect(url_for("watchlist.index"))

@watchlist_bp.route("/add-item/<string:ticker>", methods=["POST"])
@watchlist_bp.route("/add-item/", methods=["POST"])
@login_required
def add_item(ticker=None):
    # Redirect to 'next' if provided, else fallback
    next_url = request.form.get("next")
    if next_url:
        url = next_url
    else:
        url = url_for("watchlist.index")

    stock = get_stock_master_by_ticker(ticker)
    if stock:
        folder_id = request.form.get("folder_id")

        folder = get_folder_by_id(folder_id)
        if not folder:
            flash("Invalid folder selected.", "danger")
            return redirect(url)

        # Prevent duplicates
        watchlist_item = get_watchlist_item(folder=folder, stock=stock)
        if watchlist_item:
            flash("This stock is already in the selected folder.", "warning")
            return redirect(url)

        add_watchlist_item(folder=folder, stock=stock)
        flash(f"Added stock '{ticker}' to folder '{folder.name}'.", "success")
    else:
        flash(f"Please search for a valid stock.", "warning")
    return redirect(url)

@watchlist_bp.route("/remove_item/<int:folder_id>/<string:ticker>", methods=["POST"])
@login_required
def remove_item(folder_id, ticker):
    folder = get_folder_by_id(folder_id)
    remove_watchlist_item(folder_id=folder_id, ticker=ticker)
    flash(f"Removed stock '{ticker}' from folder '{folder.name}'.", "success")
    return redirect(url_for("watchlist.index"))
