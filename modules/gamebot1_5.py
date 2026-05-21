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
    print("Starting Game 1.5 AFK bot...")

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
    confirm_game_template = os.path.join(base_dir, "templates", "confirm_game.png")  # Интерфейс подтверждения матча
    hero_select_template = os.path.join(base_dir, "templates", "hero_select.png")    # Интерфейс выбора персонажа
    in_game_template = os.path.join(base_dir, "templates", "1game_1.png")           # Интерфейс игры
    game_over_template = os.path.join(base_dir, "templates", "1game_3.png")         # Экран окончания игры
    print(f"Looking for confirm game template at: {confirm_game_template}")
    print(f"Looking for hero select template at: {hero_select_template}")
    print(f"Looking for in-game template at: {in_game_template}")
    print(f"Looking for game over template at: {game_over_template}")

    time.sleep(3)

    # 1. Подтверждаем игру по скриншоту (confirm_game.png)
    max_attempts = 60  # Максимальное количество попыток для поиска интерфейса
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for confirm game interface...")
        if find_template(screenshot_path, confirm_game_template):
            print("Confirm game interface detected!")
            break
        print("Confirm game interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Confirm game interface not detected in time.")

    # Нажимаем кнопку подтверждения матча
    confirm_coords = (950, 900)  # Координаты для подтверждения матча
    print(f"Tapping confirm game button at {confirm_coords}")
    tap(device, confirm_coords[0], confirm_coords[1])

    # Задержка 1 секунды
    print("Waiting for 1 second...")
    time.sleep(1)

    # 2. Выбираем персонажа по скриншоту (hero_select.png)
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for hero select interface...")
        if find_template(screenshot_path, hero_select_template):
            print("Hero select interface detected!")
            break
        print("Hero select interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Hero select interface not detected in time.")

    # Нажимаем кнопку выбора персонажа
    hero_select_coords = (1630, 200)  # Координаты выбора персонажа
    print(f"Tapping hero selection button at {hero_select_coords}")
    tap(device, hero_select_coords[0], hero_select_coords[1])

    # 3. Задержка 2 секунды и подтверждаем выбор персонажа
    print("Waiting for 2 seconds before confirming hero...")
    time.sleep(1.5)

    # Нажимаем кнопку подтверждения (предполагаем, что она на том же экране)
    hero_confirm_coords = (1722, 1033)  # Координаты подтверждения персонажа
    print(f"Tapping hero confirmation button at {hero_confirm_coords}")
    tap(device, hero_confirm_coords[0], hero_confirm_coords[1])

    # Задержка 3 секунды
    print("Waiting for 3 seconds...")
    time.sleep(3)

    # 4. Проверяем, что мы в игре (интерфейс 1game_1.png)
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking if in game...")
        if find_template(screenshot_path, in_game_template, threshold=0.8):
            print("In-game interface detected!")
            break
        print("In-game interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("In-game interface not detected in time.")

    # 5. Ждем окончания игры
    print("Standing at base and waiting for the game to end...")
    while True:
        screenshot_path = take_screenshot(device)

        # Проверяем экран окончания игры (1game_3.png)
        if find_template(screenshot_path, game_over_template):
            print("Game over detected!")
            break

        time.sleep(1)  # Проверяем каждую секунду

    # 6. Нажимаем кнопку подтверждения после конца игры
    print("Waiting for 1 second before confirming...")
    time.sleep(1)
    print(f"Tapping confirm game button at {confirm_coords}")
    tap(device, confirm_coords[0], confirm_coords[1])

    print("Game 1.5 AFK bot completed.")

if __name__ == "__main__":
    run()