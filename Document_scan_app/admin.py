from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from Database.data import get_pending_credit_requests, approve_credits, decline_credits
import sqlite3
from Database.data import DB_NAME
import os

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin():
    if "username" not in session or session.get("role") != "admin":
        flash("You must be an admin to access this page.", "error")
        return redirect(url_for("login"))

    print(f"Admin accessing dashboard. DB path: {os.path.abspath(DB_NAME)}")

    if request.method == "POST":
        username = request.form.get("username")
        action = request.form.get("action")
        
        if action == "approve":
            approve_credits(username)
            flash(f"Credits approved for {username}.", "success")
        elif action == "decline":
            decline_credits(username)
            flash(f"Credits declined for {username}.", "success")
        return redirect(url_for("admin.admin"))

    # Fetch pending requests
    try:
        pending_requests = get_pending_credit_requests()
        print(f"Admin dashboard - Pending requests: {pending_requests}")
    except Exception as e:
        print(f"Error in get_pending_credit_requests: {e}")
        pending_requests = []

    # Direct database check
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.username, u.credits, ar.request_date
            FROM admin_requests ar
            JOIN users u ON ar.username = u.username
            WHERE ar.status = 'Pending'
        """)
        raw_requests = cursor.fetchall()
        conn.close()
        print(f"Direct DB query - Pending requests: {raw_requests}")
    except Exception as e:
        print(f"Error in direct DB query: {e}")
        raw_requests = []

    if raw_requests and not pending_requests:
        print("Mismatch detected: Direct query found data, but get_pending_credit_requests returned empty.")

    return render_template("admin.html", pending_requests=pending_requests)