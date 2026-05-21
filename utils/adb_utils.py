import subprocess
import os
import time
from ppadb.client import Client
import cv2

# Имя команды ADB
ADB_EXEC = "adb"

def connect_adb(serial=None):
    """Подключение к устройству."""
    print(f"Connecting to ADB ({serial})...")
    if serial:
        subprocess.run([ADB_EXEC, "connect", serial], capture_output=True, timeout=5)
    
    adb = Client(host='127.0.0.1', port=5037)
    try:
        devices = adb.devices()
    except RuntimeError:
        subprocess.run([ADB_EXEC, "start-server"], capture_output=True)
        time.sleep(2)
        devices = adb.devices()

    if not devices:
        raise Exception("ADB_ERROR: No ADB devices connected.")
    
    if serial:
        device = adb.device(serial)
        if not device:
            raise Exception(f"ADB_ERROR: Device with serial {serial} not found.")
        return device
    else:
        return devices[0]

def _run_shell_safe(serial, command, timeout=10, retries=2):
    """Выполнение команд с ретраями."""
    full_cmd = [ADB_EXEC, "-s", serial, "shell", command]
    
    for attempt in range(retries + 1):
        try:
            subprocess.run(full_cmd, timeout=timeout, check=True, capture_output=True)
            return 
        except subprocess.TimeoutExpired:
            if attempt < retries:
                time.sleep(1)
                continue
            raise Exception(f"ADB_TIMEOUT: Command '{command}' timed out on {serial}")
        except subprocess.CalledProcessError as e:
            if attempt < retries:
                time.sleep(1)
                continue
            raise Exception(f"ADB_ERROR: Command failed: {e}")

def tap(device, x, y):
    _run_shell_safe(device.serial, f"input tap {x} {y}", timeout=5)
    time.sleep(0.5)

def swipe(device, x1, y1, x2, y2, duration=500):
    timeout_seconds = (duration / 1000) + 5
    _run_shell_safe(
        device.serial, 
        f"input swipe {x1} {y1} {x2} {y2} {duration}", 
        timeout=timeout_seconds
    )
    time.sleep(0.5)

def adb_input_text(device, text):
    text = text.replace(" ", "%s").replace("&", "\\&").replace("|", "\\|")
    _run_shell_safe(device.serial, f"input text '{text}'", timeout=15)
    time.sleep(0.5)

def start_app(serial, package_name, activity_name):
    real_serial = serial.serial if hasattr(serial, 'serial') else serial
    cmd = [ADB_EXEC, '-s', real_serial, 'shell', 'am', 'start', '-n', f"{package_name}/{activity_name}"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        raise Exception("ADB_TIMEOUT: start_app timed out")

def take_screenshot(device, filename=None):
    """
    Делает скриншот и сохраняет его в папку 'screenshots' в корне проекта.
    """
    # 1. Определяем путь к папке screenshots (в текущей рабочей директории)
    base_dir = os.getcwd()
    screenshots_dir = os.path.join(base_dir, "screenshots")
    
    # 2. Создаем папку, если её нет
    if not os.path.exists(screenshots_dir):
        try:
            os.makedirs(screenshots_dir)
        except OSError:
            pass # Игнорируем ошибку, если папка была создана параллельным процессом

    # 3. Генерируем имя файла, если не задано
    if filename is None:
        filename = f"screenshot_{device.serial}.png"
    
    # 4. Формируем полный путь: C:\Project\screenshots\screenshot_emulator-5554.png
    full_path = os.path.join(screenshots_dir, filename)

    # 5. Делаем скриншот
    for attempt in range(2):
        try:
            with open(full_path, "wb") as f:
                subprocess.run([ADB_EXEC, "-s", device.serial, "exec-out", "screencap", "-p"], 
                               stdout=f, timeout=10, check=True)
            return full_path # Возвращаем полный путь, чтобы cv2 мог его найти
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            if attempt == 0:
                time.sleep(1)
                continue
            raise Exception("ADB_TIMEOUT: Screenshot failed after retries")
            
    return full_path

def find_template(screenshot_path, template_path, threshold=0.7):
    """Ищет шаблон на скриншоте."""
    screenshot = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    
    if screenshot is None:
        # Добавляем инфо о пути для отладки
        raise Exception(f"Could not load screenshot: {screenshot_path}")
    if template is None:
        raise Exception(f"Could not load template: {template_path}")
        
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    
    return max_val >= threshold