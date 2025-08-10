import requests
import json
import os
import sys
import hashlib # Import hashlib for hashing password before saving to config
from get_hwid import get_hardware_id

SERVER_URL = "http://127.0.0.1:5000"
CONFIG_FILE = "app_config.json" # Still used to store the password locally for subsequent runs

def run_main_app():
    """
    This function would typically launch your actual .exe application.
    For demonstration, it just prints a success message.
    """
    print("\n--- Application Launched Successfully! ---")
    # In a real scenario, you would use subprocess.Popen to run your .exe
    # Example: subprocess.Popen(["path/to/your/app.exe"])
    # Or if it's a Python app, you might import and call its main function.

def get_user_input(prompt, is_password=False):
    """Helper to get user input, optionally masking for passwords."""
    if is_password:
        import getpass
        return getpass.getpass(prompt)
    else:
        return input(prompt)

def main():
    hardware_id = get_hardware_id()
    print(f"Your Device Hardware ID: {hardware_id}")

    password = get_user_input("Enter your password/license key: ", is_password=True)
    if not password:
        print("Password cannot be empty. Application blocked.")
        return

    # First, try to verify the password
    print("\nAttempting to verify password...")
    try:
        response = requests.post(f"{SERVER_URL}/verify", json={
            "password": password,
            "hardware_id": hardware_id # Send hardware_id for verification
        })
        result = response.json()

        if response.status_code == 200:
            status = result.get("status")
            if status == "success":
                print("Verification successful. Launching application.")
                # Save password hash to config file for future runs if not already saved
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                with open(CONFIG_FILE, 'w') as f:
                    json.dump({"password_hash": password_hash}, f)
                run_main_app()
            elif status == "first_login":
                print("Password found. This is the first login for this password on any device.")
                print("Attempting to bind hardware ID...")
                # Now, attempt to register/bind the hardware ID
                register_response = requests.post(f"{SERVER_URL}/register", json={
                    "password": password,
                    "hardware_id": hardware_id
                })
                register_result = register_response.json()

                if register_response.status_code == 200 and register_result.get("status") == "bound":
                    print("Hardware ID bound successfully. Launching application.")
                    # Save password hash to config file
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump({"password_hash": password_hash}, f)
                    run_main_app()
                elif register_response.status_code == 200 and register_result.get("status") == "already_bound":
                    print("Hardware ID already bound to this password. Launching application.")
                    # Save password hash to config file
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump({"password_hash": password_hash}, f)
                    run_main_app()
                elif register_response.status_code == 409 and register_result.get("status") == "blocked":
                    print(f"Error: {register_result.get('message')}")
                    print("This password is already in use on another device. Application blocked.")
                else:
                    print(f"An unexpected error occurred during binding: {register_result.get('message', 'No message')}")
                    print("Application blocked.")
            else:
                print(f"An unexpected status received from server: {status}. Application blocked.")
        elif response.status_code == 403 and result.get("status") == "blocked":
            print(f"Error: {result.get('message')}")
            print("This password is registered to a different device. Application blocked.")
        elif response.status_code == 404 and result.get("status") == "not_found":
            print(f"Error: {result.get('message')}")
            print("Password not found in the system. Please ensure it's pre-registered.")
            print("Application blocked.")
        else:
            print(f"An unexpected error occurred during verification: {result.get('message', 'No message')}")
            print("Application blocked.")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the license server. Please ensure the server is running.")
        print("Application blocked.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Application blocked.")

if __name__ == "__main__":
    main()
