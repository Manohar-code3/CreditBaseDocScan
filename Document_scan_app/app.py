import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
from user import user_bp
from admin import admin_bp
from Database.data import register_user, login_user, get_user_credits
# from dotenv import load_dotenv

# load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("user.user"))  # Redirect logged-in users to dashboard
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = login_user(username, password)
        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["credits"] = user["credits"]
            session["email"] = user.get("email", "")
            if user["role"] == "admin":
                return redirect(url_for("admin.admin"))
            return redirect(url_for("user.user"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "username" in session:
        return redirect(url_for("user.user"))  # Redirect logged-in users to dashboard
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        if register_user(username, email, password):
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        flash("Username or email already exists.", "error")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)