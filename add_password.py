import sqlite3
import hashlib
import getpass

DATABASE = 'users.db'

def add_password():
    """Adds a new pre-registered password to the database."""
    password = getpass.getpass("Enter the new password to pre-register: ")
    if not password:
        print("Password cannot be empty.")
        return

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            # Check if the password already exists
            cursor.execute("SELECT password_hash FROM users WHERE password_hash = ?", (password_hash,))
            if cursor.fetchone():
                print("This password is already registered.")
                return

            # Insert the new password with a NULL hardware_id
            cursor.execute("INSERT INTO users (password_hash, hardware_id) VALUES (?, NULL)", (password_hash,))
            conn.commit()
            print(f"Password has been pre-registered successfully.")

    except sqlite3.IntegrityError:
        print("Error: This password is already registered.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    # Make sure the database is initialized
    # This is safe to run multiple times
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                password_hash TEXT NOT NULL UNIQUE,
                hardware_id TEXT
            )
        ''')
        conn.commit()
    add_password()
