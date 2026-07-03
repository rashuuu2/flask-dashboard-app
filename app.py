from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def init_db():
    conn = sqlite3.connect("user.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        password TEXT,
        image TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("user.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    cursor.execute("SELECT image FROM users WHERE email=?", (session["user"],))
    img = cursor.fetchone()
    conn.close()

    return render_template("dashboard.html",
                           email=session["user"],
                           total_users=count,
                           image=img[0] if img else None)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/signup", methods=["POST"])
def signup_post():
    data = request.json
    hashed = generate_password_hash(data["password"])

    conn = sqlite3.connect("user.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                   (data["email"], hashed))
    conn.commit()
    conn.close()

    return jsonify({"message": "created"})

# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.json

    conn = sqlite3.connect("user.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE email=?", (data["email"],))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[0], data["password"]):
        session["user"] = data["email"]
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})

# UPLOAD IMAGE
@app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session:
        return redirect("/")

    file = request.files["file"]
    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    conn = sqlite3.connect("user.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET image=? WHERE email=?",
                   (path, session["user"]))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

if __name__ == "__main__":
    app.run(debug=True)