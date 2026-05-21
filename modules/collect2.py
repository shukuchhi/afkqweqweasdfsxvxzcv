import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.adb_helper import check_adb_devices

import time
import subprocess
from utils.adb_utils import connect_adb, take_screenshot, tap
from utils.image_processing import find_template

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
    interface1_template = os.path.join(base_dir, "templates", "match_podtv.png")      # Первый интерфейс
    interface2_template = os.path.join(base_dir, "templates", "collect2.png")  # Второй интерфейс
    interface4_template = os.path.join(base_dir, "templates", "collect2_2.png")
    interface5_template = os.path.join(base_dir, "templates", "lobby.png")
    print(f"Looking for first interface at: {interface1_template}")
    print(f"Looking for second interface at: {interface2_template}")

    time.sleep(2)

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
        if find_template(screenshot_path, interface1_template):
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

    time.sleep(4)

    # 3. Ждем второй интерфейс и нажимаем кнопку
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for second interface...")
        if find_template(screenshot_path, interface2_template):
            print("Second interface detected!")
            break
        tap(device, second_coords[0], second_coords[1])
        print("Second interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Second interface not detected in time.")
    
    time.sleep(3)

    one = (100, 100)
    tap(device, one[0], one[1])
    tap(device, one[0], one[1])

    time.sleep(2)

    # Нажимаем кнопку на втором интерфейсе
    third_coords = (150, 190)
    print(f"Tapping third button at {third_coords}")
    tap(device, third_coords[0], third_coords[1])
    time.sleep(0.25)
    tap(device, third_coords[0], third_coords[1])

    time.sleep(1)

    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for second interface...")
        if find_template(screenshot_path, interface2_template):
            time.sleep(1)
            attempt += 1
        time.sleep(1)
        break
    else:
        raise Exception("Second interface not detected in time.")


    # 4. Ждем 2 секунды и нажимаем на кнопку
    print("Waiting for 2 seconds...")
    time.sleep(4)
    
    heal_gift = (600,760)
    print(f"Tapping heal_gift button at {heal_gift}")
    tap(device, heal_gift[0], heal_gift[1])
    time.sleep(1)
    tap(device, heal_gift[0], heal_gift[1])
    time.sleep(2)
    confirm = (950, 960)
    print(f"Tapping confirm button at {confirm}")
    tap(device, confirm[0], confirm[1])
    
    time.sleep(13)
    darrius = (1822, 950)
    print(f"Tapping confirm button at {darrius}")
    tap(device, darrius[0], darrius[1])
    time.sleep(1)
    tap(device, darrius[0], darrius[1])
    time.sleep(0.25)
    tap(device, darrius[0], darrius[1])

    time.sleep(3)

    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for third interface...")
        if find_template(screenshot_path, interface5_template):
            print("Third interface detected!")
            break
        print("Third interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Third interface not detected in time.")

    time.sleep(2)

    # 8. Нажать на координаты
    sixth_coords = (665, 880)  # Замени на свои координаты
    print(f"Tapping sixth button at {sixth_coords}")
    tap(device, sixth_coords[0], sixth_coords[1])

    time.sleep(3.5)

    print("Reward collection for Game 2 completed.")

if __name__ == "__main__":
    run()