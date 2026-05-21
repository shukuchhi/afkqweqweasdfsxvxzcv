"""
Collect 1 — сбор наград после Game 1.
"""

import sys, os, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.adb_helper import check_adb_devices
from utils.adb_utils import connect_adb, take_screenshot, tap
from utils.image_processing import find_template


def run(serial=None):
    print("Starting Collect 1...")

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
    knopka_template   = os.path.join(base_dir, "templates", "collect1.png")
    collect2_t        = os.path.join(base_dir, "templates", "collect2.png")
    pyat_template     = os.path.join(base_dir, "templates", "pyat.png")
    interface5        = os.path.join(base_dir, "templates", "lobby.png")
    collect1_t        = os.path.join(base_dir, "templates", "collect1_1.png")

    max_attempts = 30

    # 1. Тройной тап
    first_coords = (877, 1000)
    print(f"Tapping first button at {first_coords}")
    for _ in range(3):
        tap(device, first_coords[0], first_coords[1])
        time.sleep(0.25)
    time.sleep(3)

    # Ждём knopka
    attempt = 0
    while attempt < max_attempts:
        sp = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for 'knopka' interface...")
        if find_template(sp, knopka_template):
            print("'Knopka' interface detected!")
            break
        print("'Knopka' interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("'Knopka' interface not detected in time.")

    time.sleep(2)

    continue_coords = (1737, 1000)
    print(f"Tapping 'Continue' button at {continue_coords}")
    tap(device, continue_coords[0], continue_coords[1])
    time.sleep(0.25)
    tap(device, continue_coords[0], continue_coords[1])

    print("Waiting for 1.5 seconds...")
    time.sleep(8)

    attempt = 0
    while attempt < max_attempts:
        sp = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for 'knopka' interface...")
        if find_template(sp, knopka_template):
            print("'Knopka' interface detected!")
            break
        print("'Knopka' interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("'Knopka' interface not detected in time.")

    time.sleep(4)

    second_button = (100, 200)
    print(f"Tapping second button at {second_button}")
    for _ in range(3):
        tap(device, second_button[0], second_button[1])
        time.sleep(0.25)
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

    # Ждём collect2
    attempt = 0
    while attempt < max_attempts:
        sp = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for 'collect2' interface...")
        if find_template(sp, collect2_t):
            print("'Collect2' interface detected!")
            break
        print("'Collect2' interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("'Collect2' interface not detected in time.")

    time.sleep(3)

    pyat_button = (1730, 910)
    print(f"Tapping button on 'pyat' interface at {pyat_button}")
    tap(device, pyat_button[0], pyat_button[1])
    time.sleep(1)
    tap(device, pyat_button[0], pyat_button[1])
    time.sleep(3)

    print("Reward collection and game start completed.")


if __name__ == "__main__":
    run()