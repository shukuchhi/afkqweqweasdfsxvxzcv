import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess
import time
from datetime import datetime
import pytz  # Для работы с часовыми поясами
from utils.adb_utils import connect_adb, take_screenshot, tap, adb_input_text, swipe
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

def get_server_date():
    """Получаем текущую дату сервера в часовом поясе UTC-8."""
    server_tz = pytz.timezone("America/Los_Angeles")  # UTC-8 (PDT или PST)
    server_time = datetime.now(server_tz)
    day = server_time.day  # Например, 9 для 9 мая
    month = server_time.month  # Например, 5 для мая
    print(f"Server date (UTC-8): {server_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Setting birthday to day: {day}, month: {month}")
    return day, month

def set_birthday(device, day, month):
    """Устанавливаем дату рождения в игре, нажимая на кнопки '+'."""
    day_plus_coords = (1075, 762)  # Координаты кнопки "+" для дня
    month_plus_coords = (920, 762)  # Координаты кнопки "+" для месяца

    # Начальные значения: 01 для дня и 01 для месяца
    day_clicks = day - 1  # Например, для 9 дня: 9-1 = 8 нажатий
    month_clicks = month - 1  # Например, для 5 месяца: 5-1 = 4 нажатия

    # Устанавливаем день
    print(f"Setting day to {day} by clicking {day_clicks} times at {day_plus_coords}...")
    for i in range(day_clicks):
        tap(device, day_plus_coords[0], day_plus_coords[1])
        time.sleep(0.5)  # Задержка для стабильности

    # Устанавливаем месяц
    print(f"Setting month to {month} by clicking {month_clicks} times at {month_plus_coords}...")
    for i in range(month_clicks):
        tap(device, month_plus_coords[0], month_plus_coords[1])
        time.sleep(0.5)  # Задержка для стабильности

def run(serial=None):
    """Запускает MLBB, устанавливает дату рождения и закрывает приложение."""
    print("Starting process to set birthday in MLBB...")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    interface1_template = os.path.join(base_dir, "templates", "birthday.png")      # Первый интерфейс
    print(f"Looking for first interface at: {interface1_template}")

    # Проверяем ADB
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
    
    time.sleep(2.5)
    eighth_coords = (64, 70)
    print(f"Tapping eighth button at {eighth_coords}")
    tap(device, eighth_coords[0], eighth_coords[1])

    # 9. Через 1 секунду нажимаем на (1785, 165)
    print("Waiting for 1 second...")
    time.sleep(3)
    ninth_coords = (1785, 165)
    print(f"Tapping ninth button at {ninth_coords}")
    tap(device, ninth_coords[0], ninth_coords[1])

    time.sleep(2)
    vizitka = (1835, 810)
    print(f"Tapping vizitka button at {vizitka}")
    tap(device, vizitka[0], vizitka[1])

    time.sleep(2)
    vizitka1 = (1322, 295)
    print(f"Tapping vizitka1 button at {vizitka1}")
    tap(device, vizitka1[0], vizitka1[1])

    time.sleep(2)
    
    daybirthday = (1180, 500)
    print(f"Tapping daybirthday button at {daybirthday}")
    tap(device, daybirthday[0], daybirthday[1])

    time.sleep(2)

    # Получаем текущую дату сервера
    day, month = get_server_date()

    # Устанавливаем дату рождения
    set_birthday(device, day, month)

    # Сохраняем изменения (если есть кнопка "Сохранить")
    print("Saving changes (adjust coordinates as needed)...")
    tap(device, 1272, 947)  # Замените на координаты кнопки "Сохранить" (примерные координаты)
    time.sleep(2)
    
    podtverdit = (1186, 767)
    print(f"Tapping podtverdit button at {podtverdit}")
    tap(device, podtverdit[0], podtverdit[1])

    time.sleep(2)
    
    # Останавливаем MLBB
    mlbb_package = "com.mobile.legends"
    print(f"Остановка приложения {mlbb_package}...")
    adb_cmd = ['adb']
    if serial:
        adb_cmd.extend(['-s', serial])
    adb_cmd.extend(['shell', 'am', 'force-stop', mlbb_package])
    subprocess.run(adb_cmd, check=True)

    time.sleep(5)

    open = (473, 213)
    print(f"Tapping open button at {open}")
    tap(device, open[0], open[1])
    
    time.sleep(15)

    # Внешний цикл для перезапуска поиска interface1_template (birthday.png) в случае неудачи
    while True:
        max_attempts = 30  # Максимальное количество попыток для поиска интерфейса
        attempt = 0
        birthday_interface_found = False
        while attempt < max_attempts:
            screenshot_path = take_screenshot(device)
            print(f"Attempt {attempt + 1}: Checking for birthday interface (birthday.png)...")
            if find_template(screenshot_path, interface1_template):
                print("Birthday interface (birthday.png) detected!")
                birthday_interface_found = True
                break  # Выход из внутреннего цикла попыток
            print("Birthday interface (birthday.png) not detected yet")
            time.sleep(1)
            attempt += 1

        if birthday_interface_found:
            break  # Выход из внешнего цикла перезапуска, если интерфейс найден
        else:
            # Этот блок выполняется, если interface1_template не найден после max_attempts
            print("Birthday interface (birthday.png) not detected after max_attempts. Restarting app and retrying...")
            # Останавливаем MLBB
            mlbb_package = "com.mobile.legends"
            print(f"Остановка приложения {mlbb_package}...")
            adb_cmd = ['adb']
            if serial:
                adb_cmd.extend(['-s', serial])
            adb_cmd.extend(['shell', 'am', 'force-stop', mlbb_package])
            try:
                subprocess.run(adb_cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"Error stopping app: {e.stderr}. Retrying...")
                time.sleep(5) # Даем время перед повторной попыткой
                continue # Перезапускаем внешний цикл

            time.sleep(5)

            open_coords = (473, 213)  # Используем те же координаты, что и в account_creation
            print(f"Tapping open button at {open_coords}")
            tap(device, open_coords[0], open_coords[1])

            print("Waiting 15 seconds for app to restart...")
            time.sleep(15) # Увеличена задержка для полной загрузки приложения
            continue # Перезапускаем внешний цикл (и, следовательно, процесс поиска)

    time.sleep(5)

    joystick_center = (210, 375)
    joystick_target = (400, 375)
    print("Moving joystick right-up...")
    swipe(device, joystick_center[0], joystick_center[1], joystick_target[0], joystick_target[1], duration=1000)
    time.sleep(2.5)

    birthdaybutton = (230,375)
    print(f"Tapping birthdaybutton button at {birthdaybutton}")
    tap(device, birthdaybutton[0], birthdaybutton[1])
    
    time.sleep(5)

    vecherinka = (1000, 900)
    print(f"Tapping vecherinka button at {vecherinka}")
    tap(device, vecherinka[0], vecherinka[1])
    
    time.sleep(5)
 
    podarok = (1775, 540)
    print(f"Tapping podarok button at {podarok}")
    tap(device, podarok[0], podarok[1])

    time.sleep(5)
    
    hero = (1300, 572)
    print(f"Tapping hero button at {hero}")
    tap(device, hero[0], hero[1])

    time.sleep(2)

    freya = (400,630)
    print(f"Tapping freya button at {freya}")
    tap(device, freya[0], freya[1])

    time.sleep(2)

    freya_podtverdit = (1250,900)
    print(f"Tapping freya_podtverdit button at {freya_podtverdit}")
    tap(device, freya_podtverdit[0], freya_podtverdit[1])

    time.sleep(3)

    polychit = (1300, 900)
    print(f"Tapping polychit button at {polychit}")
    tap(device, polychit[0], polychit[1])

    time.sleep(4)

    heropolychit = (1710, 1010)
    print(f"Tapping heropolychit button at {heropolychit}")
    tap(device, heropolychit[0], heropolychit[1])

    time.sleep(4)

    exitting = (50, 35)
    print(f"Tapping exitting button at {exitting}")
    tap(device, exitting[0], exitting[1])

    time.sleep(3)

    print("Birthday setting process completed!")

if __name__ == "__main__":
    run()