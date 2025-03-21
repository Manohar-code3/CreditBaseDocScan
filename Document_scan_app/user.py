from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from Database.data import get_user_credits, get_user_upload_count, save_file_to_db, compare_with_existing_files, request_credits, get_user_files, get_all_files, has_pending_request, read_document, calculate_similarity
import os
from datetime import datetime, timedelta

user_bp = Blueprint("user", __name__)

@user_bp.route("/user", methods=["GET", "POST"])
def user():
    if "username" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    username = session["username"]
    credits = get_user_credits(username)
    upload_count = get_user_upload_count(username)
    user_files = get_user_files(username)

    # Calculate time until midnight
    now = datetime.now()
    midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
    time_to_midnight = midnight - now
    hours, remainder = divmod(time_to_midnight.seconds, 3600)
    minutes = remainder // 60
    reset_time = f"{hours}h {minutes}m"

    if request.method == "POST":
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename:
                if credits <= 0:
                    flash("You have no credits left. Please request more credits.", "error")
                    return redirect(url_for("user.user"))
                
                from Database.data import allowed_file
                if not allowed_file(file.filename):
                    flash("Invalid file type. Only .txt files are allowed.", "error")
                    return redirect(url_for("user.user"))

                upload_folder = "uploads"
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, file.filename)
                file.save(file_path)
                
                similarity = save_file_to_db(username, file.filename, file_path)
                if similarity is False:
                    flash("You have no credits left. Please request more credits.", "error")
                    return redirect(url_for("user.user"))
                
                flash(f"File uploaded successfully! Max similarity: {similarity:.2f}%", "success")
                return redirect(url_for("user.results"))
        
        elif "action" in request.form and request.form["action"] == "request_credits":
            # Check if the user already has a pending request
            if has_pending_request(username):
                flash("Request already sent.", "error")
                return redirect(url_for("user.user"))

            # Check if credits are less than 15
            if credits >= 15:
                flash("Cannot send request: Credits are 15 or more.", "error")
                return redirect(url_for("user.user"))

            # If credits < 15 and no pending request, proceed with the request
            if request_credits(username):
                flash("Request sent to admin.", "success")
            else:
                flash("Failed to send request.", "error")
            return redirect(url_for("user.user"))

    return render_template("user.html", credits=credits, upload_count=upload_count, user_files=user_files, reset_time=reset_time)

@user_bp.route("/results")
def results():
    if "username" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    username = session["username"]
    credits = get_user_credits(username)
    upload_count = get_user_upload_count(username)
    user_files = get_user_files(username)

    # Calculate time until midnight
    now = datetime.now()
    midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
    time_to_midnight = midnight - now
    hours, remainder = divmod(time_to_midnight.seconds, 3600)
    minutes = remainder // 60
    reset_time = f"{hours}h {minutes}m"

    # Prepare user_results for display (user's own files)
    user_results = []
    for idx, (file_name, file_path, upload_date, similarity) in enumerate(user_files, 1):
        user_results.append({
            "file_name": file_name,
            "upload_date": upload_date,
            "type": "Text",
            "id": f"doc-{idx}",
            "extract": read_document(file_path)[:50] + "..." if read_document(file_path) else "No content",
            "similarity": round(similarity, 2)
        })

    # Get the most recent file for comparison with other users' files
    most_recent_file = user_files[0] if user_files else None
    other_users_results = []
    if most_recent_file:
        most_recent_file_path = most_recent_file[1]  # file_path
        all_files = get_all_files()
        idx = len(user_files) + 1
        for file_user, file_name, file_path, upload_date, _ in all_files:
            if file_user != username:  # Exclude the current user's files
                # Calculate similarity with the most recent file
                most_recent_text = read_document(most_recent_file_path)
                other_text = read_document(file_path)
                similarity = calculate_similarity(most_recent_text, [other_text])
                other_users_results.append({
                    "file_name": file_name,
                    "upload_date": upload_date,
                    "type": "Text",
                    "id": f"doc-{idx}",
                    "extract": other_text[:50] + "..." if other_text else "No content",
                    "similarity": round(similarity, 2)
                })
                idx += 1

    return render_template("results.html", credits=credits, upload_count=upload_count, user_results=user_results, other_users_results=other_users_results, reset_time=reset_time)