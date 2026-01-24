from flask import Blueprint
from utils.constants import PASSWORD_POLICY

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    static_folder="static"
)

from . import routes

@auth_bp.context_processor
def inject_global_constants():
    return {
        "PASSWORD_POLICY": PASSWORD_POLICY
    }