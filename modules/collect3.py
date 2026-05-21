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
    interface_template = os.path.join(base_dir, "templates", "match_podtv.png")
    interface1_template = os.path.join(base_dir, "templates", "collect3_2.png")  # Первый интерфейс
    interface2_template = os.path.join(base_dir, "templates", "pyat.png")  # Второй интерфейс
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
        if find_template(screenshot_path, interface1_template):
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
    third_coords = (1737, 1039)
    time.sleep(5)  # Замени на свои координаты
    podtverdit_graph = (1178, 770)
    print(f"Tapping third button at {podtverdit_graph}")
    tap(device, podtverdit_graph[0], podtverdit_graph[1])
    time.sleep(0.25)
    print(f"Tapping third button at {third_coords}")
    tap(device, third_coords[0], third_coords[1])
    time.sleep(0.25)
    tap(device, third_coords[0], third_coords[1])
    time.sleep(2)
    tap(device, podtverdit_graph[0], podtverdit_graph[1])
    time.sleep(2)
    tap(device, opros[0], opros[1])
    time.sleep(0.25)
    tap(device, opros[0], opros[1])
    time.sleep(0.25)
    tap(device, third_coords[0], third_coords[1])
    time.sleep(0.25)
    tap(device, third_coords[0], third_coords[1])
    time.sleep(2)
    tap(device, podtverdit_graph[0], podtverdit_graph[1])



    time.sleep(6)

    exit = (150, 50)
    print(f"Tapping exit button at {exit}")
    tap(device, exit[0], exit[1])

    time.sleep(2)

    # 4. По скриншоту collect3_2.png нажимаем на кнопку
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for second interface...")
        if find_template(screenshot_path, interface2_template):
            print("Second interface detected!")
            break
        print("Second interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Second interface not detected in time.")
    
    time.sleep(3)
    print("Waiting for 1 second...")
    time.sleep(2)

    # 17. Нажимаем на координаты
    thirteenth_coords = (1887, 1011)  # Замени на свои координаты
    print(f"Tapping thirteenth button at {thirteenth_coords}")
    tap(device, thirteenth_coords[0], thirteenth_coords[1])

    # 18. Ждем 3 секунды
    print("Waiting for 3 seconds...")
    time.sleep(3)

    # 19. Нажимаем на координаты
    fourteenth_coords = (670, 890)  # Замени на свои координаты
    print(f"Tapping fourteenth button at {fourteenth_coords}")
    tap(device, fourteenth_coords[0], fourteenth_coords[1])

    print("Reward collection for Game 3 completed.")

if __name__ == "__main__":
    run()