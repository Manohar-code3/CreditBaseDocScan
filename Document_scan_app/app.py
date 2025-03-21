from flask import Flask, render_template, request, redirect, url_for, session, flash
from Database.data import login_user, register_user
from user import user_bp
import os
from admin import admin_bp  # Adjust path if needed
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

# Register user blueprint
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return render_template("register.html")

        if register_user(username, email, password):
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

        flash("Username or email already exists. Choose another.", "error")
        return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = login_user(username, password)

        if user:
            session.clear()
            session["username"] = user["username"]
            session["role"] = user["role"]

            flash("Login successful!", "success")

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("user.user"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/admin")
def admin_dashboard():
    if "username" not in session or session.get("role") != "admin":
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    return render_template("admin.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
