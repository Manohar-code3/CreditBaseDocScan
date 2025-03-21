import sqlite3
from werkzeug.security import generate_password_hash

import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_NAME = os.path.join(BASE_DIR, "users.db")
# DB_NAME = "users.db"

# Connect to the database
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

hashed_password = generate_password_hash("admin123")

# Insert admin user (username: admin, password: admin123, role: admin)
cursor.execute("INSERT INTO users (username, password, email,role) VALUES (?, ?, ?,?)", 
               ("admin", hashed_password,"admin@gmail.com", "admin"))

# Commit and close connection
conn.commit()
conn.close()


print("Admin user added successfully!")

