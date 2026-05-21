"""
ADB Utilities — обёртки над adb_helper с авто-восстановлением соединения.
"""

import subprocess
import os
import time
import cv2

from ppadb.client import Client

# Функции из adb_helper (без ADBHelper-класса, которого не существует)
from utils.adb_helper import adb, is_online, restart_adb_server

ADB_EXEC = "adb"

# ==============================================================================
# БЕЗОПАСНЫЙ ВЫЗОВ ADB SHELL
# ==============================================================================

def adb_shell(serial: str, command: str, timeout: int = 10, retries: int = 3):
    """
    Выполнить shell-команду на устройстве с авто-восстановлением ADB.
    """
    adb(serial, 'shell', command, timeout=timeout, retries=retries)


def _run_shell_safe(serial, command, timeout=10, retries=2):
    """
    Совместимость со старым кодом — делегирует в adb_helper.
    """
    try:
        adb(serial, 'shell', command, timeout=timeout, retries=retries + 1)
    except Exception as e:
        raise Exception(f"ADB_ERROR: {e}")

# ==============================================================================
# ПОДКЛЮЧЕНИЕ К УСТРОЙСТВУ
# ==============================================================================

def connect_adb(serial=None):
    """Подключение к устройству (с авто-восстановлением если девайс пропал)."""
    print(f"Connecting to ADB ({serial})...")

    if serial:
        if not is_online(serial):
            restart_adb_server()
            time.sleep(3)
    else:
        subprocess.run([ADB_EXEC, "start-server"], capture_output=True, timeout=5)

    client = Client(host='127.0.0.1', port=5037)
    try:
        devices = client.devices()
    except RuntimeError:
        subprocess.run([ADB_EXEC, "start-server"], capture_output=True)
        time.sleep(2)
        devices = client.devices()

    if not devices:
        raise Exception("ADB_ERROR: No ADB devices connected.")

    if serial:
        device = client.device(serial)
        if not device:
            raise Exception(f"ADB_ERROR: Device with serial {serial} not found.")
        return device
    else:
        return devices[0]

# ==============================================================================
# ТАПЫ / СВАЙПЫ / ВВОД
# ==============================================================================

def tap(device, x, y):
    _run_shell_safe(device.serial, f"input tap {x} {y}", timeout=5)
    time.sleep(0.5)

def swipe(device, x1, y1, x2, y2, duration=500):
    timeout_seconds = (duration / 1000) + 5
    _run_shell_safe(
        device.serial,
        f"input swipe {x1} {y1} {x2} {y2} {duration}",
        timeout=timeout_seconds,
    )
    time.sleep(0.5)

def adb_input_text(device, text):
    text = text.replace(" ", "%s").replace("&", "\&").replace("|", "\|")
    _run_shell_safe(device.serial, f"input text '{text}'", timeout=15)
    time.sleep(0.5)

# ==============================================================================
# ЗАПУСК ПРИЛОЖЕНИЙ
# ==============================================================================

def start_app(serial, package_name, activity_name):
    real_serial = serial.serial if hasattr(serial, 'serial') else serial
    try:
        adb(real_serial, 'shell', 'am', 'start', '-n',
            f"{package_name}/{activity_name}", timeout=10)
    except Exception:
        raise Exception("ADB_TIMEOUT: start_app timed out")

# ==============================================================================
# СКРИНШОТЫ
# ==============================================================================

def take_screenshot(device, filename=None):
    """Делает скриншот и сохраняет в папку 'screenshots' в корне проекта."""
    screenshots_dir = os.path.join(os.getcwd(), "screenshots")

    if not os.path.exists(screenshots_dir):
        try:
            os.makedirs(screenshots_dir)
        except OSError:
            pass

    if filename is None:
        filename = f"screenshot_{device.serial}.png"

    full_path = os.path.join(screenshots_dir, filename)

    for attempt in range(2):
        try:
            with open(full_path, "wb") as f:
                subprocess.run(
                    [ADB_EXEC, "-s", device.serial, "exec-out", "screencap", "-p"],
                    stdout=f, timeout=10, check=True,
                )
            return full_path
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            if attempt == 0:
                restart_adb_server()
                time.sleep(1)
                continue
            raise Exception("ADB_TIMEOUT: Screenshot failed after retries")

    return full_path

# ==============================================================================
# ПОИСК ШАБЛОНА
# ==============================================================================

def find_template(screenshot_path, template_path, threshold=0.7):
    """Ищет шаблон на скриншоте."""
    screenshot = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
    template   = cv2.imread(template_path,   cv2.IMREAD_GRAYSCALE)

    if screenshot is None:
        raise Exception(f"Could not load screenshot: {screenshot_path}")
    if template is None:
        raise Exception(f"Could not load template: {template_path}")

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return max_val >= threshold
