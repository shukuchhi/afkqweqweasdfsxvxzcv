"""
Game 1.5 AFK Bot — подтверждение матча → выбор героя → игра (AFK) → конец.
"""

import sys, os, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.adb_helper import check_adb_devices
from utils.adb_utils import connect_adb, take_screenshot, tap
from utils.image_processing import find_template


def run(serial=None):
    print("Starting Game 1.5 AFK bot...")

    if not check_adb_devices():
        print("Exiting due to ADB connection issues.")
        return

    print("Attempting to connect to device...")
    try:
        device = connect_adb(serial)
        print("Device connected successfully!")
    except Exception as e:
        print(f"Error connecting to device: {e}")
        return

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    confirm_game = os.path.join(base_dir, "templates", "confirm_game.png")
    hero_select  = os.path.join(base_dir, "templates", "hero_select.png")
    in_game      = os.path.join(base_dir, "templates", "1game_1.png")
    game_over    = os.path.join(base_dir, "templates", "1game_3.png")

    print(f"Templates loaded.")
    time.sleep(3)

    max_attempts = 60

    # 1. Подтверждение матча
    attempt = 0
    while attempt < max_attempts:
        sp = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for confirm game interface...")
        if find_template(sp, confirm_game):
            print("Confirm game interface detected!")
            break
        print("Confirm game interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Confirm game interface not detected in time.")

    tap(device, 950, 900)
    print("Waiting for 1 second...")
    time.sleep(1)

    # 2. Выбор героя
    attempt = 0
    while attempt < max_attempts:
        sp = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for hero select interface...")
        if find_template(sp, hero_select):
            print("Hero select interface detected!")
            break
        print("Hero select interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Hero select interface not detected in time.")

    tap(device, 1630, 200)
    print("Waiting for 2 seconds before confirming hero...")
    time.sleep(1.5)
    tap(device, 1722, 1033)
    print("Waiting for 3 seconds...")
    time.sleep(3)

    # 3. В игре
    attempt = 0
    while attempt < max_attempts:
        sp = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking if in game...")
        if find_template(sp, in_game, threshold=0.8):
            print("In-game interface detected!")
            break
        print("In-game interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("In-game interface not detected in time.")

    # 4. Ждём конца
    print("Standing at base and waiting for the game to end...")
    while True:
        sp = take_screenshot(device)
        if find_template(sp, game_over):
            print("Game over detected!")
            break
        time.sleep(1)

    print("Waiting for 1 second before confirming...")
    time.sleep(1)
    tap(device, 950, 900)
    print("Game 1.5 AFK bot completed.")


if __name__ == "__main__":
    run()