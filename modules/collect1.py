import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import subprocess  # Для проверки ADB
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
    print("Starting Game 1 AFK bot...")

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
    knopka_template = os.path.join(base_dir, "templates", "collect1.png")  # Кнопка "Продолжить"
    collect2 = os.path.join(base_dir, "templates", "collect2.png")
    pyat_template = os.path.join(base_dir, "templates", "pyat.png")      # Второй интерфейс
    interface5_template = os.path.join(base_dir, "templates", "lobby.png")
    print(f"Looking for 'knopka' template at: {knopka_template}")
    print(f"Looking for 'pyat' template at: {pyat_template}")
    collect1 = os.path.join(base_dir, "templates", "collect1_1.png")

    # 1. Нажимаем по координате
    first_coords = (877, 1000)
    print(f"Tapping first button at {first_coords}")
    tap(device, first_coords[0], first_coords[1])
    time.sleep(0.25)
    tap(device, first_coords[0], first_coords[1])
    time.sleep(0.55)
    tap(device, first_coords[0], first_coords[1])
    
    time.sleep(3)

    # 1. Ждем интерфейс "knopka.png" и нажимаем кнопку "Продолжить"
    max_attempts = 30  # Максимальное количество попыток для поиска интерфейса
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for 'knopka' interface...")
        if find_template(screenshot_path, knopka_template):
            print("'Knopka' interface detected!")
            break
        print("'Knopka' interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("'Knopka' interface not detected in time.")
    
    time.sleep(2)

    # Нажимаем кнопку "Продолжить"
    continue_coords = (1737, 1000)
    print(f"Tapping 'Continue' button at {continue_coords}")
    tap(device, continue_coords[0], continue_coords[1])
    time.sleep(0.25)
    tap(device, continue_coords[0], continue_coords[1])

    # 2. Ждем 1.5 секунды и нажимаем кнопку на координатах
    print("Waiting for 1.5 seconds...")
    time.sleep(8)

    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for 'knopka' interface...")
        if find_template(screenshot_path, knopka_template):
            print("'Knopka' interface detected!")
            break
        print("'Knopka' interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("'Knopka' interface not detected in time.")

    time.sleep(4)
    
    second_button_coords = (100, 200)
    print(f"Tapping second button at {second_button_coords}")
    tap(device, second_button_coords[0], second_button_coords[1])
    time.sleep(0.25)
    tap(device, second_button_coords[0], second_button_coords[1])
    time.sleep(0.25)
    tap(device, second_button_coords[0], second_button_coords[1])

    time.sleep(12)

    skip = (328, 558)
    print(f"Tapping skip button at {skip}")
    tap(device, skip[0], skip[1])
    time.sleep(0.25)
    tap(device, skip[0], skip[1])

    time.sleep(10)

    podtverdit_layla = (1656, 945)
    print(f"Tapping second button at {podtverdit_layla}")
    tap(device, podtverdit_layla[0], podtverdit_layla[1])
    time.sleep(0.25)
    tap(device, podtverdit_layla[0], podtverdit_layla[1])
    
    time.sleep(3)


    # 3. Ждем интерфейс "pyat.png" и нажимаем кнопку
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for 'knopka' interface...")
        if find_template(screenshot_path, collect2):
            print("'Knopka' interface detected!")
            break
        print("'Knopka' interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("'Knopka' interface not detected in time.")
    
    time.sleep(3)

    # Нажимаем кнопку на интерфейсе "pyat"
    pyat_button_coords = (1730,910)
    print(f"Tapping button on 'pyat' interface at {pyat_button_coords}")
    tap(device, pyat_button_coords[0], pyat_button_coords[1])
    time.sleep(1)
    tap(device, pyat_button_coords[0], pyat_button_coords[1])

    time.sleep(3)

    print("Reward collection and game start completed.")

if __name__ == "__main__":
    run()