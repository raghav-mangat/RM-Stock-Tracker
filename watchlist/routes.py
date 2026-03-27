from . import watchlist_bp
from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from models.database import AlertAttribute
from .services import AjaxService, Validators, ActionContext, ExceptionService, MutationHandler
from utils.status_files import db_last_updated
from utils.market_status import get_complete_market_status
from utils.db_queries.watchlist import *

"""
Watchlist Routes - Architectural Overview

These routes follow a thin-controller pattern:

1. Routes are responsible only for:
   - Reading request data
   - Detecting AJAX vs non-AJAX requests
   - Orchestrating validation, mutation (updating the DB), and response handling

2. Input validation is performed via Validators, which raise ValidationError
   for user-correctable issues.

3. Database mutations are executed in db_queries util functions, which:
   - Return MutationResult for expected business conflicts (e.g. duplicates)
   - Raise domain exceptions (NotFoundError, ForbiddenError) for invalid state

4. MutationHandler centralizes success/warning responses for both
   AJAX (JSON) and non-AJAX (flash + redirect) flows.

5. ExceptionService centralizes error-to-response mapping, ensuring:
   - Consistent user messaging
   - Correct HTTP status codes
   - Appropriate UI behavior (e.g. refresh hints)

This structure keeps routes small, predictable, and consistent across
all watchlist actions.
"""

@watchlist_bp.route('', methods=["GET"])
def index():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    if not current_user.is_authenticated:
        return render_template("watchlist_loggedout.html", last_updated=last_updated)

    watchlist_data = db_get_all_watchlist_data(current_user)
    num_folders = db_get_num_folders(current_user)

    return render_template(
        "watchlist_loggedin.html",
        watchlist_data=watchlist_data,
        num_folders=num_folders,
        FolderAttribute=FolderAttribute,
        AlertAttribute=AlertAttribute,
        OrderBy=OrderBy,
        last_updated=last_updated,
        market_status=get_complete_market_status()
    )

@watchlist_bp.route("/alerts", methods=["GET"])
@login_required
def alerts():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    watchlist_alert_data = db_get_all_watchlist_data(current_user)
    num_user_alerts = len(get_all_user_watchlist_alerts(current_user))

    return render_template(
        "watchlist_alerts.html",
        watchlist_alert_data=watchlist_alert_data,
        num_user_alerts=num_user_alerts,
        last_updated=last_updated,
        market_status=get_complete_market_status()
    )

@watchlist_bp.route("/about", methods=["GET"])
@login_required
def about():
    return render_template(
        "watchlist_about.html",
    )

@watchlist_bp.route("/add-folder", methods=["POST"])
@login_required
def add_folder():
    # Redirect to 'next' if provided, else fallback
    next_url = request.form.get("next") or url_for("watchlist.index")

    folder_name = request.form.get("folder_name")

    try:
        folder_name = Validators.validate_folder_name(folder_name)
        result = db_add_folder(folder_name, current_user)
        return MutationHandler.response(result, is_ajax=False, next_url=next_url)
    except Exception as exc:
        ctx = ActionContext("add", "folder")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=False, next_url=next_url)

@watchlist_bp.route("/rename-folder/<int:folder_id>", methods=["POST"])
@login_required
def rename_folder(folder_id):
    AjaxService.require_ajax()

    new_folder_name = request.form.get("new_folder_name")

    try:
        folder_name = Validators.validate_folder_name(new_folder_name)
        result = db_rename_folder(folder_name, folder_id, current_user)
        return MutationHandler.response(result, is_ajax=True)

    except Exception as exc:
        ctx = ActionContext("rename", "folder")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=True)

@watchlist_bp.route("/remove-folder", methods=["POST"])
@login_required
def remove_folder():
    folder_id = request.form.get("folder_id")

    try:
        result = db_remove_folder(folder_id=folder_id, user=current_user)
        return MutationHandler.response(result)
    except Exception as exc:
        ctx = ActionContext("remove", "folder")
        return ExceptionService.handle_action_exception(exc, ctx)

@watchlist_bp.route("/update-order/<int:folder_id>", methods=["POST"])
@login_required
def update_order(folder_id):
    new_order = int(request.form.get("order"))
    try:
        max_order = Validators.validate_folder_order(current_user, new_order)
        result = db_update_order(folder_id, new_order, max_order, current_user)
        return MutationHandler.response(result)
    except Exception as exc:
        ctx = ActionContext("reorder", "folder")
        return ExceptionService.handle_action_exception(exc, ctx)

@watchlist_bp.route("/add-item", methods=["POST"])
@login_required
def add_item():
    # Check if the request is AJAX
    is_ajax = AjaxService.is_ajax()

    # Redirect to 'next' if provided, else fallback
    next_url = request.form.get("next") or url_for("watchlist.index")

    ticker = request.form.get("ticker")
    folder_id = request.form.get("folder_id")

    try:
        ticker_master = Validators.validate_ticker(ticker)
        result = db_add_watchlist_item(folder_id=folder_id, ticker=ticker_master, user=current_user)

        return MutationHandler.response(result, is_ajax=is_ajax, next_url=next_url)

    except Exception as exc:
        ctx = ActionContext("add", "stock")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=is_ajax, next_url=next_url)

@watchlist_bp.route("/remove-item/<int:item_id>", methods=["POST"])
@login_required
def remove_item(item_id):
    AjaxService.require_ajax()

    try:
        result = db_remove_watchlist_item(item_id=item_id, user=current_user)
        return MutationHandler.response(result, is_ajax=True)

    except Exception as exc:
        ctx = ActionContext("remove", "stock")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=True)

@watchlist_bp.route("/update-folder-alerts/<int:folder_id>", methods=["POST"])
@login_required
def update_folder_alerts(folder_id):
    AjaxService.require_ajax()

    try:
        validated_alerts = Validators.validate_alerts(request)
        result = db_update_folder_alerts(folder_id, validated_alerts, current_user)
        return MutationHandler.response(result, is_ajax=True)

    except Exception as exc:
        ctx = ActionContext("update", "folder alerts")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=True)

@watchlist_bp.route("/update-item-alerts/<int:item_id>", methods=["POST"])
@login_required
def update_item_alerts(item_id):
    AjaxService.require_ajax()

    try:
        validated_alerts = Validators.validate_alerts(request)
        result = db_update_item_alerts(item_id, validated_alerts, current_user)
        return MutationHandler.response(result, is_ajax=True)

    except Exception as exc:
        ctx = ActionContext("update", "stock alerts")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=True)

@watchlist_bp.route("/update-folder-attributes/<int:folder_id>", methods=["POST"])
@login_required
def update_folder_attributes(folder_id):
    AjaxService.require_ajax()

    try:
        action, selected_attributes = Validators.validate_attributes(request)
        result = db_update_folder_attributes(folder_id, action, selected_attributes, current_user)
        return MutationHandler.response(result, is_ajax=True)

    except Exception as exc:
        ctx = ActionContext("update attributes for", "folder")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=True)

@watchlist_bp.route("/update-folder-sort-by/<int:folder_id>", methods=["POST"])
@login_required
def update_folder_sort_by(folder_id):
    AjaxService.require_ajax()

    sort_by_attribute = request.form.get("sort_by_attribute")
    sort_by_order = request.form.get("sort_by_order")

    try:
        Validators.validate_sort_by(sort_by_attribute, sort_by_order)
        result = db_update_folder_sort_by(folder_id, sort_by_attribute, sort_by_order, current_user)
        return MutationHandler.response(result, is_ajax=True)

    except Exception as exc:
        ctx = ActionContext("update sorting for", "folder")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=True)

@watchlist_bp.route("/update-attribute-filters", methods=["POST"])
@login_required
def update_attribute_filters():
    AjaxService.require_ajax()

    try:
        attribute_id, use_abs, min_value, max_value = Validators.validate_attribute_filters(request)
        result = db_update_attribute_filters(attribute_id, use_abs, min_value, max_value, current_user)
        return MutationHandler.response(result, is_ajax=True)

    except Exception as exc:
        ctx = ActionContext("update filters for", "folder")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=True)

@watchlist_bp.route("/folder/<int:folder_id>/partial", methods=["GET"])
@login_required
def folder_partial(folder_id):
    AjaxService.require_ajax()

    try:
        folder = check_and_get_user_folder(folder_id, current_user)

        folder_data = db_get_folder_with_items_data(folder)
        num_folders = db_get_num_folders(current_user)

        folder_header = render_template(
            "partials/folder_header.html",
            folder_id=folder_id,
            folder_data=folder_data,
        )
        folder_body = render_template(
            "partials/folder_body.html",
            folder_id=folder_id,
            folder_data=folder_data,
            num_folders=num_folders,
            FolderAttribute=FolderAttribute,
            AlertAttribute=AlertAttribute,
            OrderBy=OrderBy,
        )

        return jsonify({
            "html": {
                "folder_header": folder_header,
                "folder_body": folder_body,
            }
        })

    except Exception as exc:
        ctx = ActionContext("access", "folder")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=True)

@watchlist_bp.route("/alert/folder/<int:folder_id>/partial", methods=["GET"])
@login_required
def alert_folder_partial(folder_id):
    AjaxService.require_ajax()

    try:
        folder = check_and_get_user_folder(folder_id, current_user)

        alert_folder_data = db_get_watchlist_alert_folder_data(folder)

        alert_folder_body = render_template(
            "partials/alert_folder_body.html",
            alert_folder_data=alert_folder_data,
            AlertAttribute=AlertAttribute,
        )

        return jsonify({
            "html": {
                "alert_folder_body": alert_folder_body,
            }
        })

    except Exception as exc:
        ctx = ActionContext("access", "folder")
        return ExceptionService.handle_action_exception(exc, ctx, is_ajax=True)

@watchlist_bp.route("/refresh", methods=["GET"])
@login_required
def refresh():
    # Get the message and category from the query parameter
    message = request.args.get('message', 'Action Failed.')
    category = request.args.get('category', 'danger')

    # Flash the message
    flash(message, category)

    # Redirect to watchlist
    return redirect(url_for('watchlist.index'))