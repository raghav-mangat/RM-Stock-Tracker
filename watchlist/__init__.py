from flask import Blueprint

watchlist_bp = Blueprint(
    "watchlist",
    __name__,
    template_folder="templates",
    static_folder="static"
)

from . import routes