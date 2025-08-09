import subprocess
import hashlib
import platform

def get_hardware_id():
    """
    Generates a unique hardware ID based on system information.
    Attempts to use motherboard serial, CPU ID, and disk serial.
    """
    hwid_components = []

    # Get Motherboard Serial Number (Windows/Linux)
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("wmic baseboard get serialnumber", shell=True).decode().strip()
            serial = output.split('\n')[1].strip()
            if serial:
                hwid_components.append(serial)
        except Exception as e:
            print(f"Could not get motherboard serial (Windows): {e}")
    elif platform.system() == "Linux":
        try:
            output = subprocess.check_output("sudo dmidecode -s baseboard-serial-number", shell=True).decode().strip()
            if output:
                hwid_components.append(output)
        except Exception as e:
            print(f"Could not get motherboard serial (Linux): {e}")

    # Get CPU ID (Windows/Linux)
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("wmic cpu get processorid", shell=True).decode().strip()
            cpu_id = output.split('\n')[1].strip()
            if cpu_id:
                hwid_components.append(cpu_id)
        except Exception as e:
            print(f"Could not get CPU ID (Windows): {e}")
    elif platform.system() == "Linux":
        try:
            output = subprocess.check_output("grep -E '^(cpu serial|processor|model name)' /proc/cpuinfo | head -n 1", shell=True).decode().strip()
            if output:
                hwid_components.append(output)
        except Exception as e:
            print(f"Could not get CPU ID (Linux): {e}")

    # Get Disk Serial Number (Windows/Linux)
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("wmic diskdrive get serialnumber", shell=True).decode().strip()
            # Take the first non-empty serial number
            for line in output.split('\n')[1:]:
                serial = line.strip()
                if serial:
                    hwid_components.append(serial)
                    break
        except Exception as e:
            print(f"Could not get disk serial (Windows): {e}")
    elif platform.system() == "Linux":
        try:
            output = subprocess.check_output("sudo hdparm -I /dev/sda | grep 'Serial Number'", shell=True).decode().strip()
            serial = output.split(':')[-1].strip()
            if serial:
                hwid_components.append(serial)
        except Exception as e:
            print(f"Could not get disk serial (Linux): {e}")

    # Fallback if no specific hardware info is found (less unique but better than nothing)
    if not hwid_components:
        hwid_components.append(platform.node()) # Network name of the computer
        hwid_components.append(platform.machine()) # Machine type
        hwid_components.append(platform.processor()) # Processor type

    # Combine and hash the components
    combined_string = "-".join(sorted(list(set(hwid_components)))) # Use set to remove duplicates, then sort for consistency
    if not combined_string:
        # If still empty, generate a random ID (last resort)
        import uuid
        combined_string = str(uuid.uuid4())
        print("Warning: Unable to retrieve sufficient hardware info. Generating a less unique ID.")

    return hashlib.sha256(combined_string.encode()).hexdigest()

if __name__ == "__main__":
    print(f"Generated Hardware ID: {get_hardware_id()}")
