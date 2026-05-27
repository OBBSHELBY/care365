import os
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = "care365secretkey"
CORS(app)
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)
# DATABASE SETUP
def get_db():
    conn = sqlite3.connect("care365.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            health_goal TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            testosterone REAL,
            estrogen REAL,
            blood_sugar REAL,
            cholesterol REAL,
            weight REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

# HASH PASSWORD
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── ROUTES ──────────────────────────────────────────

# SIGNUP
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    first_name  = data.get("first_name")
    last_name   = data.get("last_name")
    email       = data.get("email")
    password    = hash_password(data.get("password"))
    age         = data.get("age")
    gender      = data.get("gender")
    health_goal = data.get("health_goal")

    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO users (first_name, last_name, email, password, age, gender, health_goal)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, password, age, gender, health_goal))
        conn.commit()
        conn.close()
        return jsonify({"message": "Account created successfully!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists."}), 400

# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = data.get("email")
    password = hash_password(data.get("password"))

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, password)
    ).fetchone()
    conn.close()

    if user:
        session["user_id"]   = user["id"]
        session["user_name"] = user["first_name"]
        return jsonify({"message": "Login successful!", "name": user["first_name"], "user_id": user["id"]}), 200
    else:
        return jsonify({"error": "Invalid email or password."}), 401

# LOG READING
@app.route("/log", methods=["POST"])
def log_reading():
    data = request.get_json()
    user_id      = data.get("user_id")
    date         = data.get("date")
    testosterone = data.get("testosterone")
    estrogen     = data.get("estrogen")
    blood_sugar  = data.get("blood_sugar")
    cholesterol  = data.get("cholesterol")
    weight       = data.get("weight")

    conn = get_db()
    conn.execute("""
        INSERT INTO readings (user_id, date, testosterone, estrogen, blood_sugar, cholesterol, weight)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, date, testosterone, estrogen, blood_sugar, cholesterol, weight))
    conn.commit()
    conn.close()
    return jsonify({"message": "Reading saved!"}), 201

# GET READINGS
@app.route("/readings/<int:user_id>", methods=["GET"])
def get_readings(user_id):
    conn     = get_db()
    readings = conn.execute(
        "SELECT * FROM readings WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in readings]), 200

# ── START ────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))