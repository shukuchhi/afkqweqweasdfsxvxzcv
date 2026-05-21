import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import subprocess
from utils.adb_utils import connect_adb, tap, swipe

def check_adb_devices():
    """Проверяем, есть ли подключенные устройства через ADB."""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        print("ADB devices output:")
        print(result.stdout)
        if "device" not in result.stdout:
            print("No devices found via ADB. Please ensure your emulator is running and connected.")
            return False 
        return True
    except Exception as e:
        print(f"Error checking ADB devices: {e}")
        return False

def run(serial=None):
    print("Starting collect8...")

    # Проверяем ADB перед подключением
    if not check_adb_devices():
        print("Exiting due to ADB connection issues.")
        return

    # Подключение к устройству
    print("Attempting to connect to device...")
    try:
        device = connect_adb(serial)
        print("Device connected successfully!")
    except Exception as e:
        print(f"Error connecting to device: {e}")
        return
    
    time.sleep(1)
    
    cards200 = (70, 500)
    tap(device, cards200[0], cards200[1])

    time.sleep(5)

    otmena = (1622, 169)
    print(f"Tap otmena button at {otmena}")
    tap(device, otmena[0], otmena[1])

    time.sleep(2.5)

    swipe(device, 245, 1000, 245, 500, duration=500)
    swipe(device, 245, 1000, 245, 500, duration=500)
    swipe(device, 245, 1000, 245, 500, duration=500)

    time.sleep(4)
    
    cards2250 = (244, 286)
    tap(device, cards2250[0], cards2250[1])

    time.sleep(2)
    cards2 = (1589, 880)
    tap(device, cards2[0], cards2[1])

    time.sleep(3)
    cards20 = (600, 965)
    tap(device, cards20[0], cards20[1])

    time.sleep(1.5)
    nazad = (109, 40)
    tap(device, nazad[0], nazad[1])

    print("Reward collection for collect8 completed.")

if __name__ == "__main__":
    run()