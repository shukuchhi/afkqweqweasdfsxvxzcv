"""
Game 1 AFK Bot — ждёт в игре до окончания, нажимает подтверждение.
"""

import sys, os, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.adb_helper import check_adb_devices
from utils.adb_utils import connect_adb, take_screenshot, tap
from utils.image_processing import find_template


def run(serial=None):
    print("Starting Game 1 AFK bot...")

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
    in_game   = os.path.join(base_dir, "templates", "1game_1.png")
    game_over = os.path.join(base_dir, "templates", "1game_3.png")

    print(f"Looking for in-game template at: {in_game}")
    print(f"Looking for game over template at: {game_over}")
    time.sleep(1)

    max_attempts = 60
    attempt = 0
    while attempt < max_attempts:
        sp = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking if in game...")
        if find_template(sp, in_game):
            print("In-game interface detected!")
            break
        print("In-game interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("In-game interface not detected in time.")

    print("Standing at base and waiting for the game to end...")
    while True:
        sp = take_screenshot(device)
        if find_template(sp, game_over, threshold=0.8):
            print("Game over detected!")
            break
        time.sleep(1)

    print("Waiting for 1 second before confirming...")
    time.sleep(1)

    confirm_coords = (950, 900)
    print(f"Tapping confirm game button at {confirm_coords}")
    tap(device, confirm_coords[0], confirm_coords[1])
    print("Game 1 AFK bot completed.")


if __name__ == "__main__":
    run()