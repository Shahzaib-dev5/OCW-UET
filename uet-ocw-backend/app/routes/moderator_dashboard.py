"""Backend staff workspace for reviewing instructor course submissions."""

from flask import Blueprint, redirect, render_template, url_for


moderator_dashboard_bp = Blueprint("moderator_dashboard", __name__)


@moderator_dashboard_bp.route("/moderator", methods=["GET"])
def moderator_index():
    return redirect(url_for("moderator_dashboard.moderator_dashboard"))


@moderator_dashboard_bp.route("/moderator/dashboard", methods=["GET"])
def moderator_dashboard():
    # The page shell contains no course data. All data and review decisions are
    # protected by the moderation API's server-side role checks.
    return render_template("moderator_dashboard.html")
