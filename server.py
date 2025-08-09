from flask import Flask, request, jsonify
import sqlite3
import hashlib
import os

app = Flask(__name__)
DATABASE = 'users.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                password_hash TEXT NOT NULL UNIQUE,
                hardware_id TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    password = data.get('password')
    hardware_id = data.get('hardware_id')

    if not password or not hardware_id:
        return jsonify({"message": "Password and hardware_id are required"}), 400

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (password_hash, hardware_id) VALUES (?, ?)",
                           (password_hash, hardware_id))
            conn.commit()
            return jsonify({"message": "User registered successfully"}), 201
        except sqlite3.IntegrityError:
            # This means the password_hash already exists (unique constraint)
            # Check if the existing entry has the same hardware_id
            cursor.execute("SELECT hardware_id FROM users WHERE password_hash = ?", (password_hash,))
            existing_hwid = cursor.fetchone()
            if existing_hwid and existing_hwid[0] == hardware_id:
                return jsonify({"message": "User already registered with this device"}), 200
            else:
                return jsonify({"message": "Password already in use on another device"}), 409
        except Exception as e:
            return jsonify({"message": f"An error occurred: {e}"}), 500

@app.route('/verify', methods=['POST'])
def verify_user():
    data = request.get_json()
    password = data.get('password')
    hardware_id = data.get('hardware_id')

    if not password or not hardware_id:
        return jsonify({"message": "Password and hardware_id are required"}), 400

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hardware_id FROM users WHERE password_hash = ?", (password_hash,))
        result = cursor.fetchone()

        if result:
            stored_hardware_id = result[0]
            if stored_hardware_id == hardware_id:
                return jsonify({"message": "Verification successful", "status": "success"}), 200
            else:
                return jsonify({"message": "Password registered to a different device", "status": "blocked"}), 403
        else:
            return jsonify({"message": "User not found", "status": "not_found"}), 404

if __name__ == '__main__':
    init_db()
    # For production, use a more robust WSGI server like Gunicorn or uWSGI
    # For development, you can run it directly:
    # app.run(debug=True, host='0.0.0.0', port=5000)
    # Using a specific host and port for clarity
    app.run(host='127.0.0.1', port=5000)
