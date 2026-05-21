import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import subprocess  # Для проверки ADB
from utils.adb_utils import connect_adb, take_screenshot, tap  # Убедимся, что tap импортирован
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
    in_game_template = os.path.join(base_dir, "templates", "1game_1.png")    # Интерфейс игры
    game_over_template = os.path.join(base_dir, "templates", "1game_3.png")  # Экран окончания игры
    print(f"Looking for in-game template at: {in_game_template}")
    print(f"Looking for game over template at: {game_over_template}")

    time.sleep(1)

    # 1. Проверяем, что мы в игре (интерфейс 1game_1.png)
    max_attempts = 60 
    max_attempts1 = 600 # Максимальное количество попыток для поиска интерфейса
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking if in game...")
        if find_template(screenshot_path, in_game_template):
            print("In-game interface detected!")
            break

        print("In-game interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("In-game interface not detected in time.")

    # 2. Ничего не делаем, просто ждем окончания игры
    print("Standing at base and waiting for the game to end...")
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        # 3. Проверяем экран окончания игры (1game_3.png)
        if find_template(screenshot_path, game_over_template, threshold=0.8):
            print("Game over detected!")
            break

    # Даем игре время стабилизироваться после конца игры
    print("Waiting for 1 second before confirming...")
    time.sleep(1)

    # 4. Нажимаем кнопку подтверждения
    confirm_coords = (950, 900)  # Координаты для подтверждения
    print(f"Tapping confirm game button at {confirm_coords}")
    tap(device, confirm_coords[0], confirm_coords[1])
    
    print("Game 1 AFK bot comple    ted.")

if __name__ == "__main__":
    run()