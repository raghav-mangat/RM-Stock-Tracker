from models.database import AlertAttribute
from utils.db_queries.watchlist import check_duplicate_folder

class Validators:
    @staticmethod
    def validate_folder_name(folder_name, user):
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
        elif check_duplicate_folder(folder_name, user):
            result["message"] = f"Folder '{folder_name}' already exists."
        else:
            result["valid"] = True
            result["folder_name"] = folder_name

        return result

    @staticmethod
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

                (min_value, max_value, message) = Validators.validate_values(alert["min_value"], alert["max_value"])

                if message:
                    break
                else:
                    alert["min_value"] = min_value
                    alert["max_value"] = max_value

        return message

    @staticmethod
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
