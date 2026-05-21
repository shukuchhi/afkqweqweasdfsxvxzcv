import sys
import os
import string
import secrets
import time
import json
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.adb_utils import connect_adb, take_screenshot, tap, swipe, start_app, adb_input_text
from utils.image_processing import find_template

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

def generate_nickname():
    """Генерирует случайный никнейм из букв и цифр, длина от 6 до 12 символов."""
    length = secrets.randbelow(7) + 6  # Длина от 6 до 12
    characters = string.ascii_lowercase + string.digits  # a-z и 0-9
    nickname = ''.join(secrets.choice(characters) for _ in range(length))
    return nickname

def launch_app(serial, package_name):
    """Запускает приложение через am start."""
    print(f"Запуск {package_name}...")

    component = _get_main_activity(serial, package_name)
    print(f"[DEBUG] Запускаем компонент: {component}")

    result = subprocess.run(
        ['adb', '-s', serial, 'shell', 'am', 'start', '-n', component],
        capture_output=True,
        text=True
    )

    output = (result.stdout + result.stderr).strip()
    print(f"[DEBUG] am start output: {output!r}")

    if result.returncode != 0 or 'Error' in output or 'error' in output:
        raise RuntimeError(f"ADB_ERROR: Не удалось запустить {package_name}.\n{output}")

    print(f"Готово!")


def _get_main_activity(serial, package_name):
    """Находит главную Activity через cmd package resolve-activity."""

    result = subprocess.run(
        [
            'adb', '-s', serial, 'shell',
            'cmd', 'package', 'resolve-activity',
            '--brief', package_name
        ],
        capture_output=True,
        text=True
    )

    print(f"[DEBUG] resolve-activity output: {result.stdout!r}")

    # Парсим вывод — ищем строку с package/Activity
    for line in result.stdout.strip().split('\n'):
        line = line.strip()
        # Формат строки: "com.mobile.legends/com.some.Activity"
        if '/' in line and package_name in line:
            return line

    raise RuntimeError(
        f"ADB_ERROR: Не удалось определить Activity для {package_name}.\n"
        f"Вывод: {result.stdout!r}"
    )

def clear_text(device):
    """Очищает активное поле ввода через ADB, удаляя символы по одному."""
    try:
        for _ in range(20):
            device.shell('input keyevent KEYCODE_DEL')
        print("Поле ввода очищено.")
    except Exception as e:
        print(f"Ошибка при очистке поля ввода: {e}")

def set_nickname(device, nickname, nickname_input_coords):
    """Устанавливает сгенерированный никнейм в игре."""
    print(f"Устанавливаем никнейм: {nickname}")
    tap(device, nickname_input_coords[0], nickname_input_coords[1])
    time.sleep(1)
    clear_text(device)
    time.sleep(1)
    adb_input_text(device, nickname)
    time.sleep(1)
    screen_coords = (100, 100)
    tap(device, screen_coords[0], screen_coords[1])
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
    interface_1_template = os.path.join(base_dir, "templates", "interface_1.png")
    nicknamesettings = os.path.join(base_dir, "templates", "nickname.png")
    interface_2_template = os.path.join(base_dir, "templates", "interface_2.png")
    interface_3_template = os.path.join(base_dir, "templates", "interface_3.png")
    final = os.path.join(base_dir, "templates", "collect3_1.png")
    final2 = os.path.join(base_dir, "templates", "final2.png")
    usloviya_template = os.path.join(base_dir, "templates", "usloviya.png")

    print(f"Looking for template 1 at: {interface_1_template}")
    print(f"Looking for template 2 at: {interface_2_template}")
    print(f"Looking for template 3 at: {interface_3_template}")
    print(f"Looking for usloviya at: {usloviya_template}")

    time.sleep(20)

    # =============================================
    # Поиск первого интерфейса с обработкой условий
    # =============================================
    mlbb_package = "com.mobile.legends"
    max_attempts = 60
    attempt = 0
    first_interface_found = False

    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for first interface...")

        if find_template(screenshot_path, interface_1_template):
            print("First interface detected!")
            first_interface_found = True
            break

        print("First interface not detected, checking for usloviya...")

        if find_template(screenshot_path, usloviya_template):
            print("Usloviya screen detected! Tapping through conditions...")
            tap(device, 960, 960)
            time.sleep(1)
            tap(device, 310, 561)
            tap(device, 301, 645)
            tap(device, 304, 728)
            tap(device, 1188, 889)
            time.sleep(5)
            print("Conditions tapped, returning to search loop...")
            # Не увеличиваем attempt, сразу возвращаемся в цикл
            continue

        print("Neither interface detected, waiting...")
        time.sleep(secrets.randbelow(2) + 1)  # Ждём 1-2 секунды случайно
        attempt += 1

    if not first_interface_found:
        raise Exception("ебал мать разрабов")

    # =============================================
    # Установка никнейма
    # =============================================
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
            print(f"Attempt {attempt + 1}: Checking for nickname settings screen...")
            if find_template(screenshot_path, nicknamesettings):
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
            print(f"Attempt {retry_count} failed. Nickname settings screen not detected in 30 checks.")
            if retry_count >= 3:
                raise Exception("Игра залагала на установке ника")
            print("Retrying with new nickname...")
            continue

    time.sleep(7)

    # =============================================
    # Нажатие оставшихся кнопок после ника
    # =============================================
    remaining_buttons = [
        (1440, 500),
        (1700, 940)
    ]
    for x, y in remaining_buttons:
        print(f"Tapping button at ({x}, {y})")
        tap(device, x, y)
        time.sleep(4)

    # Ждём второй интерфейс
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for second interface...")
        if find_template(screenshot_path, interface_2_template):
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

    # =============================================
    # Туториал — движения и тапы
    # =============================================
    joystick_center = (233, 842)
    joystick_target = (360, 715)
    print("Moving joystick right-up...")
    swipe(device, joystick_center[0], joystick_center[1], joystick_target[0], joystick_target[1], duration=2000)
    time.sleep(2.5)

    double_tap_coords = (1775, 919)
    print(f"Double tapping at {double_tap_coords}")
    tap(device, double_tap_coords[0], double_tap_coords[1])
    time.sleep(1.3)
    tap(device, double_tap_coords[0], double_tap_coords[1])

    time.sleep(3)

    second_tap_coords = (1477, 644)
    print(f"Tapping at {second_tap_coords}")
    tap(device, second_tap_coords[0], second_tap_coords[1])

    time.sleep(3)

    third_tap_coords = (1578, 739)
    print(f"Tapping at {third_tap_coords}")
    tap(device, third_tap_coords[0], third_tap_coords[1])

    time.sleep(10)

    print(f"Tapping at {third_tap_coords}")
    tap(device, third_tap_coords[0], third_tap_coords[1])
    time.sleep(1)
    time.sleep(1.3)
    tap(device, double_tap_coords[0], double_tap_coords[1])

    time.sleep(6)

    first_set_of_three = [
        (1374, 847),
        (1473, 945),
        (1578, 739)
    ]
    print("Tapping on first set of three coordinates...")
    for x, y in first_set_of_three:
        print(f"Tapping at ({x}, {y})")
        tap(device, x, y)
        time.sleep(3)

    time.sleep(2)

    second_set_of_three = [
        (1477, 644),
        (1578, 739),
        (1766, 159)
    ]
    print("Tapping on second set of three coordinates...")
    for x, y in second_set_of_three:
        print(f"Tapping at ({x}, {y})")
        tap(device, x, y)
        time.sleep(1)

    time.sleep(1.5)

    four_tap_coords = (1682, 529)
    print(f"Tapping at {four_tap_coords}")
    tap(device, four_tap_coords[0], four_tap_coords[1])

    time.sleep(12)

    set_of_four = [
        (1682, 529),
        (1461, 944),
        (1579, 745),
        (1777, 626),
        (1461, 944)
    ]
    print("Tapping on four coordinates...")
    for x, y in set_of_four:
        print(f"Tapping at ({x}, {y})")
        tap(device, x, y)
        time.sleep(1.5)

    time.sleep(12.5)

    single_tap_coords = (955, 884)
    print(f"Tapping at {single_tap_coords}")
    tap(device, single_tap_coords[0], single_tap_coords[1])

    time.sleep(2.5)

    joystick_center_2 = (233, 842)
    joystick_target_2 = (360, 715)
    print("Moving joystick right-up for 5 seconds...")
    swipe(device, joystick_center_2[0], joystick_center_2[1], joystick_target_2[0], joystick_target_2[1], duration=5000)

    triple_tap_coords = (1775, 919)
    print(f"Triple tapping at {triple_tap_coords}")
    for _ in range(3):
        tap(device, triple_tap_coords[0], triple_tap_coords[1])
        time.sleep(0.5)

    time.sleep(5)

    print("Tapping on set_of_four...")
    for x, y in set_of_four:
        print(f"Tapping at ({x}, {y})")
        tap(device, x, y)

    # Ждём третий интерфейс
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for third interface...")
        if find_template(screenshot_path, interface_3_template):
            print("Third interface detected!")
            break
        print("Third interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        print("баг")

    final_three_taps = [
        (1000, 1000),
        (928, 1002),
    ]
    print("Tapping on final coordinates...")
    for x, y in final_three_taps:
        print(f"Tapping at ({x}, {y})")
        tap(device, x, y)
        time.sleep(2)

    time.sleep(2)

    # Ждём final2
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for final2 interface...")
        if find_template(screenshot_path, final2):
            print("Final2 interface detected!")
            break
        print("Final2 interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Final2 interface not detected in time.")

    time.sleep(2)

    finall2 = (1700, 1000)
    print(f"Tapping at {finall2}")
    tap(device, finall2[0], finall2[1])
    time.sleep(1)

    # Ждём final (collect3_1)
    attempt = 0
    while attempt < max_attempts:
        screenshot_path = take_screenshot(device)
        print(f"Attempt {attempt + 1}: Checking for final interface...")
        if find_template(screenshot_path, final):
            print("Final interface detected!")
            break
        print("Final interface not detected yet")
        time.sleep(1)
        attempt += 1
    else:
        raise Exception("Final interface not detected in time.")

    time.sleep(1)

    finall = (1646, 942)
    print(f"Tapping at {finall}")
    tap(device, finall[0], finall[1])
    time.sleep(7)

    print(f"Tapping at {finall}")
    tap(device, finall[0], finall[1])

    # =============================================
    # Сохранение состояния
    # =============================================
    state_file = os.path.join(base_dir, "state.json")
    print(f"Writing level=1 to {state_file}")
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
        else:
            state = {}
        state['level'] = 1
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=4)
        print("Successfully updated state.json with level=1")
    except Exception as e:
        print(f"Error writing to state.json: {e}")

    print("Account creation and tutorial step completed.")

if __name__ == "__main__":
    run()