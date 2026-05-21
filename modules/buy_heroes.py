import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import subprocess
from utils.adb_utils import connect_adb, tap

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

def adb_input_text1(device, text):
    """Вводит текст через ADBKeyboard с поддержкой кириллицы."""
    try:
        # Экранируем кавычки и специальные символы для команды shell
        escaped_text = text.replace('"', '\\"')
        command = f'am broadcast -a ADB_INPUT_TEXT --es msg "{escaped_text}"'
        device.shell(command)
        print(f"Введен текст: {text}")
    except Exception as e:
        print(f"Ошибка при вводе текста через ADBKeyboard: {e}")

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

    time.sleep(3)

    shop = (70, 353)
    print(f"Tapping button at {shop}")
    tap(device, shop[0], shop[1])

    time.sleep(2)

    hero = (147, 400)
    print(f"Tap hero button at {hero}")
    tap(device, hero[0], hero[1])

    time.sleep(2)

    search = (505, 50)
    print(f"Tap search button at {search}")
    tap(device, search[0], search[1])

    time.sleep(1)

    hero1 = "Эйдора"
    hero2 = "Сабер"
    hero3 = "Тигрил"

    # Ввод первого героя
    adb_input_text1(device, hero1)
    time.sleep(1)
    cancel = (100, 100)
    tap(device, cancel[0], cancel[1])

    time.sleep(1)
    tap(device, cancel[0], cancel[1])
    time.sleep(1)
    buy = (435, 710)
    print(f"Tap buy button at {buy}")
    tap(device, buy[0], buy[1])
    time.sleep(2)
    podtverdit = (1188, 850)
    print(f"Tap confirm button at {podtverdit}")
    tap(device, podtverdit[0], podtverdit[1])
    time.sleep(2)
    podtverdit2 = (1193, 770)
    print(f"Tap confirm button at {podtverdit2}")
    tap(device, podtverdit2[0], podtverdit2[1])
    time.sleep(2)
    tap(device, podtverdit2[0], podtverdit2[1])
    time.sleep(5)
    end = (1715, 1017)
    print(f"Tap end button at {end}")
    tap(device, end[0], end[1])
    time.sleep(2)
    cleartext = (810, 50)
    print(f"Tap cleartext button at {cleartext}")
    tap(device, cleartext[0], cleartext[1])

    time.sleep(2)

    # Ввод второго героя
    search = (505, 50)
    print(f"Tap search button at {search}")
    tap(device, search[0], search[1])
    adb_input_text1(device, hero2)
    time.sleep(1)
    tap(device, cancel[0], cancel[1])
    time.sleep(1)
    print(f"Tap buy button at {buy}")
    tap(device, buy[0], buy[1])
    time.sleep(2)
    tap(device, podtverdit[0], podtverdit[1])
    time.sleep(2)
    tap(device, podtverdit2[0], podtverdit2[1])
    time.sleep(5)
    tap(device, end[0], end[1])
    time.sleep(2)
    tap(device, cleartext[0], cleartext[1])

    time.sleep(2)

    # Ввод третьего героя
    search = (505, 50)
    print(f"Tap search button at {search}")
    tap(device, search[0], search[1])
    adb_input_text1(device, hero3)
    time.sleep(1)
    tap(device, cancel[0], cancel[1])
    time.sleep(1)
    print(f"Tap buy button at {buy}")
    tap(device, buy[0], buy[1])
    time.sleep(2)
    tap(device, podtverdit[0], podtverdit[1])
    time.sleep(2)
    tap(device, podtverdit2[0], podtverdit2[1])
    time.sleep(5)
    tap(device, end[0], end[1])
    time.sleep(2)
    tap(device, cleartext[0], cleartext[1])

    time.sleep(3)

    exitting = (123, 40)
    print(f"Tap exitting button at {exitting}")
    tap(device, exitting[0], exitting[1])

if __name__ == "__main__":
    run()