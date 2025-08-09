import requests
import json
import os
import sys
from get_hwid import get_hardware_id

SERVER_URL = "http://127.0.0.1:5000"
CONFIG_FILE = "app_config.json"

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

    # Check if config file exists (means user has run before)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        password = config.get('password')
        if not password:
            print("Error: Configuration file corrupted. Please re-register.")
            os.remove(CONFIG_FILE) # Remove corrupted file
            main() # Restart registration process
            return

        print("\nVerifying existing registration...")
        try:
            response = requests.post(f"{SERVER_URL}/verify", json={
                "password": password,
                "hardware_id": hardware_id
            })
            result = response.json()

            if response.status_code == 200 and result.get("status") == "success":
                print("Verification successful. Launching application.")
                run_main_app()
            elif response.status_code == 403 and result.get("status") == "blocked":
                print(f"Error: {result.get('message')}")
                print("This password is registered to a different device. Application blocked.")
            elif response.status_code == 404 and result.get("status") == "not_found":
                print(f"Error: {result.get('message')}")
                print("Your previous registration was not found. Please re-register.")
                os.remove(CONFIG_FILE) # Remove old config
                main() # Restart registration process
            else:
                print(f"An unexpected error occurred during verification: {result.get('message', 'No message')}")
                print("Application blocked.")

        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the license server. Please ensure the server is running.")
            print("Application blocked.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print("Application blocked.")

    else:
        # First run: Register the user
        print("\n--- First run: Please register your application ---")
        password = get_user_input("Enter your password/license key: ", is_password=True)

        try:
            response = requests.post(f"{SERVER_URL}/register", json={
                "password": password,
                "hardware_id": hardware_id
            })
            result = response.json()

            if response.status_code == 201 or (response.status_code == 200 and "already registered" in result.get("message", "")):
                print(f"Registration successful: {result.get('message')}")
                # Save password to config file for future runs
                with open(CONFIG_FILE, 'w') as f:
                    json.dump({"password": password}, f)
                print("Configuration saved. Launching application.")
                run_main_app()
            elif response.status_code == 409:
                print(f"Error: {result.get('message')}")
                print("This password is already in use on another device. Application blocked.")
            else:
                print(f"Registration failed: {result.get('message', 'No message')}")
                print("Application blocked.")

        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the license server. Please ensure the server is running.")
            print("Application blocked.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print("Application blocked.")

if __name__ == "__main__":
    main()
