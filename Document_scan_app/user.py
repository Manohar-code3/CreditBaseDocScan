from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
from Database.data import  UPLOAD_FOLDER, allowed_file, save_file_to_db, compare_with_existing_files, request_credits, get_user_credits, get_pending_credit_requests
import os

user_bp = Blueprint("user", __name__)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def has_pending_request(username):
    requests = get_pending_credit_requests()
    has_pending = any(req["username"] == username for req in requests)
    print(f"Checking pending request for {username}: {has_pending}, Requests: {requests}")
    return has_pending

@user_bp.route("/user", methods=["GET", "POST"])
def user():
    if "username" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    username = session["username"]
    credits = get_user_credits(username)
    pending_request = has_pending_request(username)
    print(f"User: {username}, Credits: {credits}, Pending: {pending_request}")

    if request.method == "POST":
        if "request_credits" in request.form:
            if credits > 15:
                flash("Request can't send. You have more than 15 credits.", "error")
            elif pending_request:
                flash("Request already sent.", "error")
            else:
                if request_credits(username):
                    flash("Request sent to admin.", "success")
                    print(f"Request sent for {username}")
                else:
                    flash("Failed to send credit request. Try again.", "error")
                    print(f"Request failed for {username}")
            return redirect(url_for("user.user"))

        if credits <= 0:
            flash("No credits left! Wait for tomorrow or request credits from admin.", "error")
            return redirect(url_for("user.user"))

        file = request.files.get("file")
        if not file or file.filename == "":
            flash("No file selected!", "error")
            return redirect(url_for("user.user"))

        if not allowed_file(file.filename):
            flash("Invalid file type! Please upload a supported file format.", "error")
            return redirect(url_for("user.user"))

        filename = f"{username}_{secure_filename(file.filename)}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        try:
            file.save(filepath)
        except Exception as e:
            flash(f"Failed to save file: {str(e)}", "error")
            return redirect(url_for("user.user"))

        similarity = save_file_to_db(username, filename, filepath)
        if similarity is False:
            flash("Upload failed due to insufficient credits.", "error")
            return redirect(url_for("user.user"))

        credits = get_user_credits(username)  # Refresh credits
        flash("File uploaded successfully!", "success")
        session.pop("user_comparisons", None)
        session.pop("all_users_comparisons", None)

        user_comparisons, all_users_comparisons = compare_with_existing_files(username, filepath)
        user_comparisons = [{"uploaded_file": u[1], "compared_file": u[0], "similarity": u[2]} for u in user_comparisons]
        all_users_comparisons = [{"uploaded_file": a[1], "compared_file": a[0], "similarity": a[2]} for a in all_users_comparisons]

        session["user_comparisons"] = user_comparisons
        session["all_users_comparisons"] = all_users_comparisons

        return redirect(url_for("user.user"))

    return render_template(
        "user.html",
        username=username,
        credits=credits,
        user_comparisons=session.get("user_comparisons", []),
        all_users_comparisons=session.get("all_users_comparisons", []),
        pending_request=pending_request
    )