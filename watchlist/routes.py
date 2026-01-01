from . import watchlist_bp
from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from models.database import AlertAttribute
from .services import AjaxService, Validators, get_alerts
from utils.populate_db_info import db_last_updated
from utils.db_queries.watchlist import *

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
        last_updated=last_updated
    )

@watchlist_bp.route("/alerts", methods=["GET"])
@login_required
def alerts():
    # Load last updated timestamp of populate db
    last_updated = db_last_updated()

    watchlist_alert_data = db_get_watchlist_alert_data(current_user)

    return render_template(
        "watchlist_alerts.html",
        watchlist_alert_data=watchlist_alert_data,
        AlertAttribute=AlertAttribute,
        last_updated=last_updated
    )

@watchlist_bp.route("/add-folder", methods=["POST"])
@login_required
def add_folder():
    # Redirect to 'next' if provided, else fallback
    next_url = request.form.get("next") or url_for("watchlist.index")

    folder_name = request.form.get("folder_name")
    folder_name_result = Validators.validate_folder_name(folder_name, current_user)
    if folder_name_result["valid"]:
        try:
            db_add_folder(folder_name_result["folder_name"], current_user)
        except Exception:
            flash("An error occurred while adding the folder.", "danger")
        else:
            flash(f"Folder '{folder_name_result["folder_name"]}' added successfully.", "success")
    else:
        flash(folder_name_result["message"], "warning")

    return redirect(next_url)

@watchlist_bp.route("/rename-folder/<int:folder_id>", methods=["POST"])
@login_required
def rename_folder(folder_id):
    AjaxService.require_ajax()

    new_folder_name = request.form.get("new_folder_name")

    result = Validators.validate_folder_name(new_folder_name, current_user)
    if not result["valid"]:
        return AjaxService.error(
            message=result["message"],
            category="warning",
            status_code=400,
        )

    try:
        db_rename_folder(result["folder_name"], folder_id, current_user)

    except NotFoundError:
        return AjaxService.error(
            message="Folder not found.",
            status_code=404,
        )

    except ForbiddenError:
        return AjaxService.error(
            message="Not authorized to rename this folder.",
            status_code=403,
        )

    except Exception:
        return AjaxService.error(
            message="An error occurred while renaming the folder.",
            status_code=500,
        )

    return AjaxService.success(
        f"Folder renamed to '{result['folder_name']}'."
    )

@watchlist_bp.route("/remove-folder/<int:folder_id>", methods=["POST"])
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

@watchlist_bp.route("/update-order/<int:folder_id>", methods=["POST"])
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

@watchlist_bp.route("/add-item", methods=["POST"])
@login_required
def add_item():
    # Check if the request is AJAX
    is_ajax = AjaxService.is_ajax()

    # Redirect to 'next' if provided, else fallback
    next_url = request.form.get("next") or url_for("watchlist.index")

    ticker = request.form.get("ticker")
    stock = get_stock_master_by_ticker(ticker)

    if not stock:
        message = f"Please search for a valid stock."
        category = "warning"
        if is_ajax:
            return AjaxService.error(message=message, category=category, status_code=400)

        flash(message, category)
        return redirect(next_url)

    folder_id = request.form.get("folder_id")

    try:
        db_add_watchlist_item(folder_id=folder_id, stock=stock, user=current_user)

    except NotFoundError:
        message = "Folder not found."
        category = "danger"
        status_code = 404

    except ForbiddenError:
        message = "Not authorized to add stock to this folder."
        category = "danger"
        status_code = 403

    except DuplicateError:
        message = "This stock is already in the selected folder."
        category = "warning"
        status_code = 400

    except Exception:
        message = "An error occurred while adding stock to this folder."
        category = "danger"
        status_code = 500

    else:
        message = f"Added stock '{ticker}'."

        if is_ajax:
            return AjaxService.success(message)

        flash(message, "success")
        return redirect(next_url)

    # Error fallback
    if is_ajax:
        return AjaxService.error(message=message, category=category, status_code=status_code)

    flash(message, category)
    return redirect(next_url)

@watchlist_bp.route("/remove-item/<int:folder_id>/<string:ticker>", methods=["POST"])
@login_required
def remove_item(folder_id, ticker):
    AjaxService.require_ajax()

    try:
        db_remove_watchlist_item(folder_id=folder_id, ticker=ticker, user=current_user)

    except NotFoundError:
        return AjaxService.error(
            message="Folder or stock not found.",
            status_code=404,
        )

    except ForbiddenError:
        return AjaxService.error(
            message="Not authorized to remove stock from this folder.",
            status_code=403,
        )

    except Exception:
        return AjaxService.error(
            message="An error occurred while removing stock from this folder.",
            status_code=500,
        )

    return AjaxService.success(
        f"Removed stock '{ticker}'."
    )

@watchlist_bp.route("/update-folder-alerts/<int:folder_id>", methods=["POST"])
@login_required
def update_folder_alerts(folder_id):
    AjaxService.require_ajax()

    folder_name = request.form.get("folder_name")

    request_alerts = get_alerts(request)
    message, validated_alerts = Validators.validate_alerts(request_alerts)

    if message:
        return AjaxService.error(
            message=message,
            category="warning",
            status_code=400,
        )

    try:
        db_update_folder_alerts(folder_id, validated_alerts, current_user)

    except NotFoundError:
        return AjaxService.error(
            message="Folder not found.",
            status_code=404,
        )

    except ForbiddenError:
        return AjaxService.error(
            message="Not authorized to update alerts for this folder.",
            status_code=403,
        )

    except Exception:
        return AjaxService.error(
            message="An error occurred while updating the alerts for this folder.",
            status_code=500,
        )

    return AjaxService.success(
        f"Updated email alerts for folder '{folder_name}'."
    )

@watchlist_bp.route("/update-item-alerts/<int:item_id>", methods=["POST"])
@login_required
def update_item_alerts(item_id):
    AjaxService.require_ajax()

    ticker = request.form.get("ticker")
    folder_name = request.form.get("folder_name")

    request_alerts = get_alerts(request)
    message, validated_alerts = Validators.validate_alerts(request_alerts)

    if message:
        return AjaxService.error(
            message=message,
            category="warning",
            status_code=400,
        )

    try:
        db_update_item_alerts(item_id, validated_alerts, current_user)

    except NotFoundError:
        return AjaxService.error(
            message="Stock not found.",
            status_code=404,
        )

    except ForbiddenError:
        return AjaxService.error(
            message="Not authorized to update alerts for this stock.",
            status_code=403,
        )

    except Exception:
        return AjaxService.error(
            message="An error occurred while updating the alerts for this stock.",
            status_code=500,
        )

    return AjaxService.success(
        f"Updated email alerts for stock '{ticker}' in folder '{folder_name}'."
    )

@watchlist_bp.route("/update-folder-attributes/<int:folder_id>", methods=["POST"])
@login_required
def update_folder_attributes(folder_id):
    AjaxService.require_ajax()

    folder_name = request.form.get("folder_name")
    action = request.form.get("edit_action")

    if not folder_name or action not in {"save", "restore"}:
        return AjaxService.error(
            message="Invalid form action.",
            status_code=400,
        )

    selected_attributes = []

    if action == "save":
        all_folder_attributes = {attr.value for attr in FolderAttribute}
        for i in range(1, len(all_folder_attributes) + 1):
            attribute = request.form.get(f"folder-attribute-{i}")
            if attribute:
                if attribute in all_folder_attributes:
                    selected_attributes.append(attribute)
                else:
                    return AjaxService.error(
                        message="Invalid folder attribute selected.",
                        status_code=400,
                    )

        min_selections = 2
        max_selections = 8
        if len(selected_attributes) < min_selections:
            return AjaxService.error(
                message=f"Select at least {min_selections} attributes",
                category="warning",
                status_code=400,
            )
        if len(selected_attributes) > max_selections:
            return AjaxService.error(
                message=f"Cannot select more than {max_selections} attributes",
                category="warning",
                status_code=400,
            )

    try:
        db_update_folder_attributes(folder_id, action, selected_attributes, current_user)

    except NotFoundError:
        return AjaxService.error(
            message="Folder not found.",
            status_code=404,
        )

    except ForbiddenError:
        return AjaxService.error(
            message="Not authorized to update attributes for this folder.",
            status_code=403,
        )

    except Exception:
        return AjaxService.error(
            message="An error occurred while updating the attributes for this folder.",
            status_code=500,
        )

    return AjaxService.success(
        f"Updated attributes for folder '{folder_name}'."
    )

@watchlist_bp.route("/update-folder-sort-by/<int:folder_id>", methods=["POST"])
@login_required
def update_folder_sort_by(folder_id):
    AjaxService.require_ajax()

    sort_by_attribute = request.form.get("sort_by_attribute")
    sort_by_order = request.form.get("sort_by_order")

    if ((sort_by_attribute not in {attr.value for attr in FolderAttribute}) or
        (sort_by_order not in {attr.value for attr in OrderBy})):
        return AjaxService.error(
            message="Invalid sort by action.",
            status_code=400,
        )

    try:
        db_update_folder_sort_by(folder_id, sort_by_attribute, sort_by_order, current_user)

    except NotFoundError:
        return AjaxService.error(
            message="Folder not found.",
            status_code=404,
        )

    except ForbiddenError:
        return AjaxService.error(
            message="Not authorized to update sorting for this folder.",
            status_code=403,
        )

    except Exception:
        return AjaxService.error(
            message="An error occurred while updating the sorting for this folder.",
            status_code=500,
        )

    return AjaxService.success(
        "Updated sorting for folder."
    )

@watchlist_bp.route("/update-attribute-filters", methods=["POST"])
@login_required
def update_attribute_filters():
    AjaxService.require_ajax()

    attribute_id = request.form.get("attribute_id", type=int)
    action = request.form.get("filter_action")

    if not attribute_id or action not in {"apply", "clear"}:
        return AjaxService.error(
            message="Invalid form action.",
            status_code=400,
        )

    use_abs = False
    (min_value, max_value, message) = (None, None, None)

    if action == "apply":
        use_abs = bool(request.form.get("use-abs"))
        min_value = request.form.get("min-value")
        max_value = request.form.get("max-value")

        (min_value, max_value, message) = Validators.validate_values(use_abs, min_value, max_value)

    if message:
        return AjaxService.error(
            message=message,
            category="warning",
            status_code=400,
        )

    try:
        db_update_attribute_filters(attribute_id, use_abs, min_value, max_value, current_user)

    except NotFoundError:
        return AjaxService.error(
            message="Attribute not found.",
            status_code=404,
        )

    except ForbiddenError:
        return AjaxService.error(
            message="Not authorized to update filters for this attribute.",
            status_code=403,
        )

    except Exception:
        return AjaxService.error(
            message="An error occurred while updating the filters for this attribute.",
            status_code=500,
        )

    return AjaxService.success(
        "Updated filters for folder."
    )

@watchlist_bp.route("/folder/<int:folder_id>/partial", methods=["GET"])
@login_required
def folder_partial(folder_id):
    AjaxService.require_ajax()

    try:
        folder = check_and_get_user_folder(folder_id, current_user)

        folder_data = db_get_folder_data(folder)
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

    except NotFoundError:
        return AjaxService.error(
            message="Folder not found.",
            status_code=404,
        )

    except ForbiddenError:
        return AjaxService.error(
            message="Not authorized to access this folder.",
            status_code=403,
        )

    except Exception:
        return AjaxService.error(
            message="An error occurred while accessing the folder.",
            status_code=500,
        )
