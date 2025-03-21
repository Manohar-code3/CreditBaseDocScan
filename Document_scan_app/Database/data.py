import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# DB_NAME = "users.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt"}
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_NAME = os.path.join(BASE_DIR, "users.db")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            credits INTEGER DEFAULT 20,
            role TEXT DEFAULT 'user'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            credits_at_request INTEGER NOT NULL,
            request_date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    conn.commit()
    conn.close()

def register_user(username, email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return False
    
    hashed_password = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
    conn.commit()
    conn.close()
    return True

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, role, credits FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        return {"username": user[0], "role": user[2], "credits": user[3]}
    return None

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_upload_count(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT COUNT(*) FROM documents
        WHERE username = ? AND strftime('%Y-%m-%d', upload_date) = ?
    """, (username, today))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_user_credits(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT credits FROM users WHERE username = ?", (username,))
    credits = cursor.fetchone()[0]
    conn.close()
    return credits

def get_existing_documents():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT file_name, file_path FROM documents")
    documents = cursor.fetchall()
    conn.close()
    return documents

def read_document(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def save_file_to_db(username, file_name, file_path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT credits FROM users WHERE username = ?", (username,))
    credits = cursor.fetchone()[0]
    
    if credits <= 0:  # Only credits matter, no upload count limit
        conn.close()
        return False
    
    new_text = read_document(file_path)
    existing_docs = get_existing_documents()
    existing_texts = [read_document(path) for _, path in existing_docs]
    similarity = calculate_similarity(new_text, existing_texts)
    
    cursor.execute("""
        INSERT INTO documents (username, file_name, file_path, upload_date) 
        VALUES (?, ?, ?, ?)
    """, (username, file_name, file_path, datetime.now()))
    cursor.execute("UPDATE users SET credits = credits - 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return similarity

def get_user_files(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT file_name, file_path 
        FROM documents 
        WHERE username = ?
    """, (username,))
    user_files = cursor.fetchall()
    conn.close()
    return user_files

def get_all_files():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, file_name, file_path 
        FROM documents
    """)
    all_files = cursor.fetchall()
    conn.close()
    return all_files

def calculate_similarity(new_text, existing_texts):
    if not existing_texts:
        return 0.0
    all_texts = [new_text] + existing_texts
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    similarities = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:])[0]
    return max(similarities) * 100 if len(similarities) > 0 else 0.0

def compare_with_existing_files(username, uploaded_file_path):
    uploaded_text = read_document(uploaded_file_path)
    user_files = get_user_files(username)
    user_results = []
    for file_name, file_path in user_files:
        existing_text = read_document(file_path)
        similarity = calculate_similarity(uploaded_text, [existing_text])
        user_results.append((file_name, os.path.basename(uploaded_file_path), round(similarity, 2)))
    all_files = get_all_files()
    all_results = []
    for file_user, file_name, file_path in all_files:
        if file_user != username:
            existing_text = read_document(file_path)
            similarity = calculate_similarity(uploaded_text, [existing_text])
            all_results.append((file_name, os.path.basename(uploaded_file_path), round(similarity, 2)))
    return user_results, all_results

def request_credits(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    credits = get_user_credits(username)
    cursor.execute("""
        INSERT INTO admin_requests (username, credits_at_request, request_date, status)
        VALUES (?, ?, ?, 'Pending')
    """, (username, credits, datetime.now().isoformat()))
    conn.commit()
    cursor.execute("SELECT id FROM admin_requests WHERE username = ? AND status = 'Pending'", (username,))
    request_id = cursor.fetchone()
    conn.close()
    print(f"Request_credits for {username}: ID {request_id}")  # Debug
    return request_id is not None

def get_pending_credit_requests():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.credits, ar.request_date
        FROM admin_requests ar
        JOIN users u ON ar.username = u.username
        WHERE ar.status = 'Pending'
    """)
    requests = cursor.fetchall()
    conn.close()
    print(f"Get_pending_credit_requests: {requests}")  # Debug
    return [{"username": req[0], "credits": req[1], "request_date": req[2]} for req in requests]

def approve_credits(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET credits = 10 WHERE username = ?", (username,))
    cursor.execute("UPDATE admin_requests SET status = 'Approved' WHERE username = ? AND status = 'Pending'", (username,))
    conn.commit()
    conn.close()

def decline_credits(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE admin_requests SET status = 'Declined' WHERE username = ? AND status = 'Pending'", (username,))
    conn.commit()
    conn.close()

init_db()