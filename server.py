from flask import Flask, request, jsonify
import sqlite3
import hashlib
import os

app = Flask(__name__)
DATABASE = 'users.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Modified schema: hardware_id can be NULL initially
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                password_hash TEXT NOT NULL UNIQUE,
                hardware_id TEXT
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
        cursor.execute("SELECT hardware_id FROM users WHERE password_hash = ?", (password_hash,))
        result = cursor.fetchone()

        if result:
            stored_hardware_id = result[0]
            if stored_hardware_id is None:
                # Password exists, but no hardware_id is bound yet. Bind it.
                cursor.execute("UPDATE users SET hardware_id = ? WHERE password_hash = ?",
                               (hardware_id, password_hash))
                conn.commit()
                return jsonify({"message": "Hardware ID bound successfully", "status": "bound"}), 200
            elif stored_hardware_id == hardware_id:
                # Password exists and is already bound to this device.
                return jsonify({"message": "User already registered with this device", "status": "already_bound"}), 200
            else:
                # Password exists but is bound to a different device.
                return jsonify({"message": "Password already in use on another device", "status": "blocked"}), 409
        else:
            # Password not found in DB. User must manually add passwords.
            return jsonify({"message": "Password not found. Please ensure it's pre-registered.", "status": "not_found"}), 404

@app.route('/verify', methods=['POST'])
def verify_user():
    data = request.get_json()
    password = data.get('password')
    hardware_id = data.get('hardware_id') # hardware_id is now optional for initial verification

    if not password:
        return jsonify({"message": "Password is required"}), 400

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hardware_id FROM users WHERE password_hash = ?", (password_hash,))
        result = cursor.fetchone()

        if result:
            stored_hardware_id = result[0]
            if stored_hardware_id is None:
                # Password exists, but no hardware ID is bound yet. This is the "first login".
                return jsonify({"message": "Password found, first login for this password.", "status": "first_login"}), 200
            else:
                # Password exists and has a hardware ID bound. Now check if it matches.
                if hardware_id and stored_hardware_id == hardware_id:
                    return jsonify({"message": "Verification successful", "status": "success"}), 200
                elif hardware_id and stored_hardware_id != hardware_id:
                    return jsonify({"message": "Password registered to a different device", "status": "blocked"}), 403
                else:
                    # This case should ideally not happen if client sends hardware_id after first_login
                    return jsonify({"message": "Hardware ID required for bound password verification", "status": "error"}), 400
        else:
            return jsonify({"message": "Password not found", "status": "not_found"}), 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
