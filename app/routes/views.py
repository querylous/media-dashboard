from flask import Blueprint, render_template

views = Blueprint("views", __name__)


@views.route("/")
def index():
    """Render the main dashboard."""
    return render_template("index.html")
