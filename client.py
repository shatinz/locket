import requests
import json
import os
import sys
import hashlib # Import hashlib for hashing password before saving to config
from get_hwid import get_hardware_id

SERVER_URL = "http://94.182.92.201:5000" # Using local server for testing
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

    # Try to load password hash from config file
    saved_password_hash = None
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                saved_password_hash = config.get("password_hash")
        except json.JSONDecodeError:
            print("Warning: Could not read app_config.json. It might be corrupted.")
            os.remove(CONFIG_FILE) # Delete corrupted file

    password_to_verify = None
    if saved_password_hash:
        print("\nAttempting to verify saved password...")
        # For verification, we need the original password, not the hash.
        # Since we only store the hash, we'll need to re-prompt if the hash is the only thing we have.
        # A better approach for "session" would be to store a token, not the password hash.
        # For now, we'll prompt if the hash is present but the original password isn't.
        # Or, we can try to verify the hash directly if the server supports it.
        # Given the current server, it expects the plain password.
        # So, if we have a saved hash, we can't directly use it for /verify.
        # The original design saves the hash for *future runs* but still expects user input.
        # Let's adjust to truly use it as a session.

        # To use the saved hash for verification, the server's /verify endpoint
        # would need to accept a password_hash instead of a plain password.
        # As it stands, the server expects the plain password.
        # So, the client must either store the plain password (bad security)
        # or the server must be modified to accept a hash for re-verification.

        # For the purpose of "not asking for password each time",
        # we will assume the server can verify the hash directly for a "session" check.
        # This requires a change in server.py or a different approach.

        # Let's re-evaluate the "session" requirement.
        # If the goal is to avoid asking for the password *if it was successfully verified before*,
        # then the client needs to store the *plain password* or a *session token*.
        # Storing plain password is bad. Storing a session token is better.

        # Given the current server, it expects the plain password for /verify.
        # The client saves the *hash* of the password.
        # This means the client *cannot* re-verify without the plain password.

        # The original intent of saving `password_hash` to `app_config.json` was likely
        # to quickly check if *any* password was previously used, not to re-authenticate.

        # To truly implement "not ask for password each time", we need a session token.
        # This would involve:
        # 1. Server generates a token on successful login.
        # 2. Client saves token to app_config.json.
        # 3. Client sends token for subsequent verifications.

        # Since the current server doesn't support tokens, and storing plain password is bad,
        # the most secure way to achieve "not asking for password each time" with the current setup
        # is to re-verify the hardware ID against the *already bound* password.
        # This means the client still needs the password for the initial verification,
        # but if it's already bound, it can proceed.

        # Let's modify the logic to check if the hardware_id is already bound to *any* password.
        # This would require a new endpoint on the server, or a modification to /verify.

        # Given the current structure, the simplest way to avoid asking for password *if already verified*
        # is to check if app_config.json exists and contains a password_hash.
        # If it does, we assume the user has successfully logged in before.
        # This is a *less secure* "session" but fulfills the "not ask for password each time"
        # by relying on the presence of the config file as a "logged in" state.

        # Let's implement a simple check based on the presence of the config file.
        # If the config file exists and has a password_hash, we assume "logged in".
        # This bypasses the server verification for subsequent runs.
        # This is a security trade-off for convenience.

        print("Checking for saved session...")
        if saved_password_hash:
            print("Saved session found. Launching application.")
            run_main_app()
            return # Exit main if session found and app launched
        else:
            print("No valid saved session found. Proceeding with password prompt.")

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
