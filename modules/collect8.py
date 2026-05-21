import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import subprocess
from utils.adb_utils import connect_adb, take_screenshot, tap
from utils.image_processing import find_template

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

    # Определяем абсолютный путь к шаблонам
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    interface_template = os.path.join(base_dir, "templates", "match_podtv.png")
    collect8_template = os.path.join(base_dir, "templates", "collect5.png")
    collect2_template = os.path.join(base_dir, "templates", "collect8.png")
    print(f"Looking for collect8 at: {collect8_template}")
    print(f"Looking for collect2 at: {collect2_template}")

    time.sleep(3)

    # 1. Нажимаем по координате
    first_coords = (877, 1000)
    print(f"Tapping first button at {first_coords}")
    tap(device, first_coords[0], first_coords[1])
    time.sleep(0.25)
    tap(device, first_coords[0], first_coords[1])
    time.sleep(0.55)
    tap(device, first_coords[0], first_coords[1])

    # 2. Ждем первый интерфейс и нажимаем кнопку
    max_attempts = 30  # Максимальное количество попыток для поиска интерфейса
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for first interface...")
        if find_template(screenshot_path, interface_template):
            print("First interface detected!")
            break
        print("First interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("First interface not detected in time.")
    
    time.sleep(1)

    # Нажимаем кнопку на первом интерфейсе
    second_coords = (1750, 990)
    print(f"Tapping second button at {second_coords}")
    tap(device, second_coords[0], second_coords[1])
    time.sleep(0.25)
    tap(device, second_coords[0], second_coords[1])
    time.sleep(0.25)

    # 3. По скриншоту collect3_1.png нажимаем на кнопку
    max_attempts = 30  # Максимальное количество попыток для поиска интерфейса
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for first interface...")
        if find_template(screenshot_path, collect8_template):
            print("First interface detected!")
            break
        print("First interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("First interface not detected in time.")
    time.sleep(1)
    opros = (1616, 170)
    tap(device, opros[0], opros[1])
    time.sleep(0.5)
    third_coords = (1737, 1039)  # Замени на свои координаты
    print(f"Tapping third button at {third_coords}")
    tap(device, third_coords[0], third_coords[1])
    time.sleep(0.25)
    tap(device, third_coords[0], third_coords[1])
    time.sleep(2)
    tap(device, opros[0], opros[1])
    time.sleep(0.25)
    tap(device, opros[0], opros[1])
    time.sleep(0.25)
    tap(device, third_coords[0], third_coords[1])
    time.sleep(0.25)
    tap(device, third_coords[0], third_coords[1])


    # 4. Через 5 секунд ищем collect8.png и нажимаем на (1477, 950)
    print("Waiting for 5 seconds...")
    time.sleep(30)
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for collect8 interface...")
        if find_template(screenshot_path, collect8_template):
            print("collect8 interface detected!")
            break
        print("collect8 interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("collect8 interface not detected in time.")
    fourth_coords = (1477, 950)
    print(f"Tapping fourth button at {fourth_coords}")
    tap(device, fourth_coords[0], fourth_coords[1])
    tap(device, fourth_coords[0], fourth_coords[1])
    tap(device, fourth_coords[0], fourth_coords[1])

    # 5. Через 5 секунд нажимаем на (959, 975)
    print("Waiting for 5 seconds...")
    time.sleep(8)
    tap(device, fourth_coords[0], fourth_coords[1])
    time.sleep(8)
    fifth_coords = (959, 975)
    print(f"Tapping fifth button at {fifth_coords}")
    tap(device, fifth_coords[0], fifth_coords[1])

    # 6. Через 2 секунды нажимаем на (140, 55)
    print("Waiting for 2 seconds...")
    time.sleep(4)
    sixth_coords = (140, 55)
    print(f"Tapping sixth button at {sixth_coords}")
    tap(device, sixth_coords[0], sixth_coords[1])

    # 7. Через 1 секунду нажимаем на (80, 55)
    print("Waiting for 1 second...")
    time.sleep(3)
    seventh_coords = (80, 55)
    print(f"Tapping seventh button at {seventh_coords}")
    tap(device, seventh_coords[0], seventh_coords[1])

    # 8. Через 1 секунду ищем collect2.png и нажимаем на (64, 70)
    print("Waiting for 1 second...")
    time.sleep(3)
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for collect2 interface...")
        if find_template(screenshot_path, collect2_template):
            print("collect2 interface detected!")
            break
        print("collect2 interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("collect2 interface not detected in time.")

    print("Reward collection for collect8 completed.")

if __name__ == "__main__":
    run()