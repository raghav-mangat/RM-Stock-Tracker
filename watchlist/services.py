from flask import request, abort, jsonify, flash, redirect, url_for, render_template
from dataclasses import dataclass
from models.database import AlertAttribute, FolderAttribute, OrderBy
from utils.db_queries.tables.ticker_master import get_valid_ticker_master_by_ticker
from utils.db_queries.watchlist import (
    NotFoundError, ForbiddenError, MutationResult
)
from utils.constants import MAX_FOLDER_NAME_LEN
from utils.filters import humanize_number


class AjaxService:
    """
    Centralized helpers for AJAX-only routes and JSON responses.
    """

    @staticmethod
    def is_ajax():
        """
        Tells if the request is made via AJAX.
        """
        return request.headers.get("X-Requested-With") == "XMLHttpRequest"

    @staticmethod
    def require_ajax():
        """
        Ensures the request is made via AJAX.
        """
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            abort(400)

    @staticmethod
    def success(message: str, **extra):
        """
        Standard success response.
        """
        category = "success"
        payload = {
            "status": "success",
            "category": category,
            "message": message,
            "toast": render_template(
                "partials/toast.html",
                category=category,
                message=message
            ),
        }
        payload.update(extra)
        return jsonify(payload), 200

    @staticmethod
    def error(message: str, category="danger", status_code=400, requires_refresh=False, **extra):
        """
        Standard error response.
        """
        payload = {
            "status": "error",
            "category": category,
            "message": message,
            "toast": render_template(
                "partials/toast.html",
                category=category,
                message=message
            ),
            "requires_refresh": requires_refresh,
        }
        payload.update(extra)
        return jsonify(payload), status_code

class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class Validators:
    @staticmethod
    def validate_folder_name(folder_name: str) -> str:
        if not folder_name:
            raise ValidationError("Folder name cannot be empty.")

        folder_name = folder_name.strip().upper()

        if len(folder_name) > MAX_FOLDER_NAME_LEN:
            raise ValidationError(
                f"Folder name must be at most {MAX_FOLDER_NAME_LEN} characters."
            )

        return folder_name

    @staticmethod
    def validate_ticker(ticker):
        ticker_master = get_valid_ticker_master_by_ticker(ticker)
        if not ticker_master:
            raise ValidationError(f"Please search for a valid stock.")
        return ticker_master

    @staticmethod
    def validate_alerts(update_alert_request):
        num_alerts = int(update_alert_request.form.get("num_alerts"))

        # Get values for all form inputs, save as dict for each alert
        alerts = []
        for i in range(1, num_alerts + 1):
            alerts.append({
                "attribute": update_alert_request.form.get(f"attribute-{i}"),
                "use_abs": bool(update_alert_request.form.get(f"use-abs-{i}")),
                "min_value": update_alert_request.form.get(f"min-value-{i}"),
                "max_value": update_alert_request.form.get(f"max-value-{i}"),
                "delete": update_alert_request.form.get(f"delete-{i}")
            })
        new_alert = {
            "attribute": update_alert_request.form.get("attribute-new"),
            "use_abs": bool(update_alert_request.form.get("use-abs-new")),
            "min_value": update_alert_request.form.get(f"min-value-new"),
            "max_value": update_alert_request.form.get(f"max-value-new"),
            "delete": None
        }
        # Add the new alert only if there was a selection made in it
        if new_alert["attribute"] or new_alert["min_value"] or new_alert["max_value"]:
            alerts.append(new_alert)

        # To keep track of attributes selected by the user
        selected_attributes = set()

        # Check if the user input is valid for all alerts
        for alert in alerts:
            if not alert["delete"]:
                attribute = alert["attribute"]
                if not attribute:
                    raise ValidationError("Please select an attribute.")
                if attribute not in list(AlertAttribute):
                    raise ValidationError("Invalid attribute selected.")
                if attribute in selected_attributes:
                    raise ValidationError(f"Duplicate alert for '{AlertAttribute(attribute).label}'. Each attribute can have only one alert.")
                selected_attributes.add(attribute)

                (min_value, max_value) = Validators.validate_values(alert["use_abs"], alert["min_value"], alert["max_value"])

                alert["min_value"] = min_value
                alert["max_value"] = max_value

        return alerts

    @staticmethod
    def validate_values(use_abs, min_value, max_value):
        # 1 Trillion (1.0 T)
        min_value_allowed = -1_000_000_000_000
        max_value_allowed = 1_000_000_000_000

        def normalize_numeric_input(value):
            if value is None:
                return None
            if isinstance(value, str):
                value = value.replace(",", "").strip()
            return value

        min_value = normalize_numeric_input(min_value)
        max_value = normalize_numeric_input(max_value)

        if not min_value and not max_value:
            raise ValidationError("Please enter a value.")
        else:
            try:
                if min_value:
                    min_value = round(float(min_value), 2)
                    if use_abs and min_value < 0:
                        raise ValidationError("Value cannot be negative if absolute value function is applied.")
                    else:
                        if min_value < min_value_allowed:
                            raise ValidationError(f"Minimum value allowed is {min_value_allowed:,} ({humanize_number(min_value_allowed)})")
                        elif min_value > max_value_allowed:
                            raise ValidationError(f"Maximum value allowed is {max_value_allowed:,} ({humanize_number(max_value_allowed)})")
                else:
                    min_value = None
                if max_value:
                    max_value = round(float(max_value), 2)
                    if use_abs and max_value < 0:
                        raise ValidationError("Value cannot be negative if absolute value function is applied.")
                    else:
                        if max_value < min_value_allowed:
                            raise ValidationError(f"Minimum value allowed is {min_value_allowed:,} ({humanize_number(min_value_allowed)})")
                        elif max_value > max_value_allowed:
                            raise ValidationError(f"Maximum value allowed is {max_value_allowed:,} ({humanize_number(max_value_allowed)})")
                else:
                    max_value = None

                if (min_value is not None) and (max_value is not None) and (min_value > max_value):
                    raise ValidationError(f"Minimum value cannot be greater than maximum value.")

            except ValueError:
                raise ValidationError("Value must be a valid number.")
        return min_value, max_value

    @staticmethod
    def validate_attributes(user_request):
        action = user_request.form.get("edit_action")
        selected_attributes = []

        if action not in {"save", "restore"}:
            raise ValidationError("Invalid form action.")

        if action == "save":
            all_folder_attributes = {attr.value for attr in FolderAttribute}
            for i in range(1, len(all_folder_attributes) + 1):
                attribute = user_request.form.get(f"folder-attribute-{i}")
                if attribute:
                    if attribute in all_folder_attributes:
                        selected_attributes.append(attribute)
                    else:
                        raise ValidationError("Invalid folder attribute selected.")

            min_selections = 2
            max_selections = 8
            if len(selected_attributes) < min_selections:
                raise ValidationError(f"Select at least {min_selections} attributes")
            if len(selected_attributes) > max_selections:
                raise ValidationError(f"Cannot select more than {max_selections} attributes")

        return action, selected_attributes

    @staticmethod
    def validate_sort_by(sort_by_attribute, sort_by_order):
        if ((sort_by_attribute not in {attr.value for attr in FolderAttribute}) or
                (sort_by_order not in {attr.value for attr in OrderBy})):
            raise ValidationError("Invalid sort by action.")

    @staticmethod
    def validate_attribute_filters(user_request):
        attribute_id = user_request.form.get("attribute_id", type=int)
        action = user_request.form.get("filter_action")

        if not attribute_id or action not in {"apply", "clear"}:
            raise ValidationError("Invalid form action.")

        use_abs = False
        (min_value, max_value) = (None, None)

        if action == "apply":
            use_abs = bool(user_request.form.get("use-abs"))
            min_value = user_request.form.get("min-value")
            max_value = user_request.form.get("max-value")

            (min_value, max_value) = Validators.validate_values(use_abs, min_value, max_value)

        return attribute_id, use_abs, min_value, max_value

@dataclass(frozen=True)
class ActionContext:
    action: str        # add, rename, delete, reorder, etc.
    resource: str      # folder, stock, item, etc.

class ExceptionService:
    @staticmethod
    def handle_action_exception(
            exc: Exception,
            context: ActionContext,
            *,
            is_ajax: bool = False,
            next_url=None
    ):
        if not next_url:
            next_url = url_for("watchlist.index")

        if isinstance(exc, ValidationError):
            message = exc.message
            status_code = 422
            category = "warning"
            requires_refresh = False

        elif isinstance(exc, NotFoundError):
            message = f"{context.resource.capitalize()} not found."
            status_code = 404
            category = "danger"
            requires_refresh = True

        elif isinstance(exc, ForbiddenError):
            message = f"Not authorized to {context.action} this {context.resource}."
            status_code = 403
            category = "danger"
            requires_refresh = True

        else:
            message = f"An error occurred while trying to {context.action} the {context.resource}."
            status_code = 500
            category = "danger"
            requires_refresh = True

        if is_ajax:
            return AjaxService.error(
                message=message,
                category=category,
                status_code=status_code,
                requires_refresh=requires_refresh,
            )

        flash(message, category)
        return redirect(next_url)

class MutationHandler:
    @staticmethod
    def response(result: MutationResult, *, is_ajax=False, next_url=None):
        if not next_url:
            next_url = url_for("watchlist.index")

        message = result.message

        if result.ok:
            category="success"
            if is_ajax:
                return AjaxService.success(
                    message=message
                )
            else:
                flash(message, category)
                return redirect(next_url)
        else:
            category = "warning"
            if is_ajax:
                return AjaxService.error(
                    message=message,
                    category=category,
                    status_code=result.status_code
                )
            else:
                flash(message, category)
                return redirect(next_url)