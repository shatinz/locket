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
            import wmi
            c = wmi.WMI()
            for board in c.Win32_BaseBoard():
                if board.SerialNumber:
                    hwid_components.append(board.SerialNumber.strip())
                    break
        except Exception as e:
            print(f"Could not get motherboard serial (WMI): {e}")
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
            import wmi
            c = wmi.WMI()
            for cpu in c.Win32_Processor():
                if cpu.ProcessorId:
                    hwid_components.append(cpu.ProcessorId.strip())
                    break
        except Exception as e:
            print(f"Could not get CPU ID (WMI): {e}")
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
            import wmi
            c = wmi.WMI()
            for disk in c.Win32_DiskDrive():
                if disk.SerialNumber:
                    hwid_components.append(disk.SerialNumber.strip())
                    break
        except Exception as e:
            print(f"Could not get disk serial (WMI): {e}")
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
