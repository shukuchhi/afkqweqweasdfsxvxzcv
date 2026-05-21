"""
Account Creation — создание нового аккаунта MLBB.
"""

import sys, os, string, secrets, time, subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.adb_helper import check_adb_devices

from utils.adb_helper import adb, check_adb_devices, get_devices
from utils.adb_utils import connect_adb, take_screenshot, tap, swipe, start_app, adb_input_text
from utils.image_processing import find_template


def generate_nickname():
    length = secrets.randbelow(7) + 6
    chars = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def _get_main_activity(serial, package_name):
    result = subprocess.run(
        ['adb', '-s', serial, 'shell', 'cmd', 'package', 'resolve-activity', '--brief', package_name],
        capture_output=True, text=True,
    )
    print(f"[DEBUG] resolve-activity output: {result.stdout!r}")
    for line in result.stdout.strip().split('\n'):
        line = line.strip()
        if '/' in line and package_name in line:
            return line
    raise RuntimeError(f"ADB_ERROR: Не удалось определить Activity для {package_name}.\n{result.stdout!r}")


def launch_app(serial, package_name):
    print(f"Запуск {package_name}...")
    component = _get_main_activity(serial, package_name)
    print(f"[DEBUG] Запускаем компонент: {component}")
    try:
        adb(serial, 'shell', 'am', 'start', '-n', component)
    except RuntimeError as e:
        raise RuntimeError(f"ADB_ERROR: Не удалось запустить {package_name}.\n{e}")
    print("Готово!")


def clear_text(device):
    try:
        for _ in range(20):
            device.shell('input keyevent KEYCODE_DEL')
        print("Поле ввода очищено.")
    except Exception as e:
        print(f"Ошибка при очистке поля ввода: {e}")


def set_nickname(device, nickname, nickname_input_coords):
    print(f"Устанавливаем никнейм: {nickname}")
    tap(device, nickname_input_coords[0], nickname_input_coords[1])
    time.sleep(1)
    clear_text(device)
    time.sleep(1)
    adb_input_text(device, nickname)
    time.sleep(1)
    tap(device, 100, 100)
    print("Никнейм установлен.")


def run(serial=None):
    print("Starting Account Creation...")

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

    interface_1 = os.path.join(base_dir, "templates", "interface_1.png")
    nicknameset  = os.path.join(base_dir, "templates", "nickname.png")
    interface_2  = os.path.join(base_dir, "templates", "interface_2.png")
    interface_3  = os.path.join(base_dir, "templates", "interface_3.png")
    final_t      = os.path.join(base_dir, "templates", "collect3_1.png")
    final2       = os.path.join(base_dir, "templates", "final2.png")
    usloviya     = os.path.join(base_dir, "templates", "usloviya.png")

    print(f"Looking for templates...")
    time.sleep(20)

    mlbb_package = "com.mobile.legends"
    max_attempts = 60
    attempt = 0
    first_interface_found = False

    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for first interface...")
        if find_template(screenshot_path, interface_1):
            print("First interface detected!")
            first_interface_found = True
            break
        print("First interface not detected, checking for usloviya...")
        if find_template(screenshot_path, usloviya):
            print("Usloviya screen detected! Tapping through conditions...")
            tap(device, 960, 960)
            time.sleep(1)
            tap(device, 310, 561)
            tap(device, 301, 645)
            tap(device, 304, 728)
            tap(device, 1188, 889)
            time.sleep(5)
            print("Conditions tapped, returning to search loop...")
            continue
        print("Neither interface detected, waiting...")
        time.sleep(secrets.randbelow(2) + 1)
        attempt += 1

    if not first_interface_found:
        raise Exception("ебал мать разрабов")

    # Никнейм
    nickname_input_coords = (1444, 450)
    first_button = (1485, 775)
    retry_count = 0

    while retry_count < 3:
        nickname = generate_nickname()
        set_nickname(device, nickname, nickname_input_coords)
        time.sleep(2)

        print(f"Tapping button at {first_button}")
        tap(device, first_button[0], first_button[1])
        time.sleep(4)

        attempt = 0
        interface_2_found = False
        while attempt < 30:
            screenshot_path = take_screenshot(device)
            print(f"Attempt {attempt+1}: Checking for nickname settings screen...")
            if find_template(screenshot_path, nicknameset):
                print("Nickname settings screen detected!")
                interface_2_found = True
                break
            print("Nickname settings screen not detected yet")
            time.sleep(1)
            attempt += 1

        if interface_2_found:
            break
        else:
            retry_count += 1
            print(f"Attempt {retry_count} failed. Retrying with new nickname...")
            if retry_count >= 3:
                raise Exception("Игра залагала на установке ника")
            continue

    time.sleep(7)

    # Оставшиеся кнопки
    for x, y in [(1440, 500), (1700, 940)]:
        print(f"Tapping button at ({x}, {y})")
        tap(device, x, y)
        time.sleep(4)

    # Ждём второй интерфейс
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for second interface...")
        if find_template(screenshot_path, interface_2):
            print("Second interface detected!")
            break
        print("Second interface not detected yet")
        time.sleep(1)
        tap(device, 1440, 500)
        time.sleep(0.2)
        tap(device, 1700, 940)
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Second interface not detected in time.")

    # Туториал
    joystick_center = (233, 842)
    joystick_target = (360, 715)
    print("Moving joystick right-up...")
    swipe(device, joystick_center[0], joystick_center[1], joystick_target[0], joystick_target[1], duration=2000)
    time.sleep(2.5)

    double_tap = (1775, 919)
    print(f"Double tapping at {double_tap}")
    tap(device, double_tap[0], double_tap[1])
    time.sleep(1.3)
    tap(device, double_tap[0], double_tap[1])
    time.sleep(3)

    tap(device, 1477, 644)
    time.sleep(3)
    tap(device, 1578, 739)
    time.sleep(10)
    tap(device, 1578, 739)
    time.sleep(1)
    time.sleep(1.3)
    tap(device, double_tap[0], double_tap[1])
    time.sleep(6)

    first_three = [(1374, 847), (1473, 945), (1578, 739)]
    print("Tapping first set of three...")
    for x, y in first_three:
        print(f"  ({x}, {y})")
        tap(device, x, y)
        time.sleep(3)
    time.sleep(2)

    second_three = [(1477, 644), (1578, 739), (1766, 159)]
    print("Tapping second set of three...")
    for x, y in second_three:
        print(f"  ({x}, {y})")
        tap(device, x, y)
        time.sleep(1)
    time.sleep(1.5)

    tap(device, 1682, 529)
    time.sleep(12)

    set_of_four = [(1682, 529), (1461, 944), (1579, 745), (1777, 626), (1461, 944)]
    print("Tapping four coordinates...")
    for x, y in set_of_four:
        print(f"  ({x}, {y})")
        tap(device, x, y)
        time.sleep(1.5)
    time.sleep(12.5)

    tap(device, 955, 884)
    time.sleep(2.5)

    print("Moving joystick right-up for 5 seconds...")
    swipe(device, joystick_center[0], joystick_center[1], joystick_target[0], joystick_target[1], duration=5000)

    print(f"Triple tapping at {double_tap}")
    for _ in range(3):
        tap(device, double_tap[0], double_tap[1])
        time.sleep(0.5)
    time.sleep(5)

    print("Tapping set_of_four again...")
    for x, y in set_of_four:
        print(f"  ({x}, {y})")
        tap(device, x, y)

    # Ждём третий интерфейс
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for third interface...")
        if find_template(screenshot_path, interface_3):
            print("Third interface detected!")
            break
        print("Third interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        print("баг")

    for x, y in [(1000, 1000), (928, 1002)]:
        print(f"Tapping at ({x}, {y})")
        tap(device, x, y)
        time.sleep(2)
    time.sleep(2)

    # Ждём final2
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for final2...")
        if find_template(screenshot_path, final2):
            print("Final2 detected!")
            break
        print("Final2 not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Final2 not detected in time.")

    time.sleep(2)
    tap(device, 1700, 1000)
    time.sleep(1)

    # Ждём final
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt+1}: Checking for final...")
        if find_template(screenshot_path, final_t):
            print("Final detected!")
            break
        print("Final not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Final not detected in time.")

    tap(device, 1700, 1000)
    time.sleep(1)
    print("Account Creation completed!")


if __name__ == "__main__":
    run()