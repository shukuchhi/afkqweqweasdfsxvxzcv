import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess
import time
from utils.adb_utils import connect_adb

# --- Вспомогательные функции ---

def get_device_serial():
    """Автоматически находит Serial первого подключенного устройства."""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        for line in lines[1:]:
            if '\tdevice' in line:
                return line.split('\t')[0]
    except Exception:
        pass
    return None

def check_directory_exists_root(serial, path):
    """Проверяет существование папки через Root."""
    adb_cmd = ['adb', '-s', serial, 'shell', f'su -c "ls -d {path}"']
    result = subprocess.run(adb_cmd, capture_output=True, text=True)
    return path in result.stdout

def reset_google_adid_via_root(serial):
    """Удаляет файл с рекламным ID (нужен Root)."""
    print("Сброс Google Advertising ID...")
    target_file = "/data/data/com.google.android.gms/shared_prefs/adid_settings.xml"
    adb_cmd = ['adb', '-s', serial, 'shell', f'su -c "rm -f {target_file}"']
    
    try:
        subprocess.run(adb_cmd, check=True)
        print("Google ID сброшен.")
        return True
    except subprocess.CalledProcessError:
        print("Не удалось сбросить ID (возможно нет Root прав).")
        return False    

def rename_directory_root(serial, old_path, new_path):
    """Переименовывает папку для сохранения кэша."""
    print(f"Переименование: {old_path} -> {new_path}")
    adb_cmd = ['adb', '-s', serial, 'shell', f'su -c "mv {old_path} {new_path}"']
    try:
        subprocess.run(adb_cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def clear_app_data(serial, package_name):
    """Моментально очищает данные приложения через команду pm clear."""
    print(f"Быстрая очистка данных {package_name}...")
    adb_cmd = ['adb', '-s', serial, 'shell', 'pm', 'clear', package_name]
    try:
        subprocess.run(adb_cmd, check=True)
        print("Данные очищены.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка очистки: {e}")

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

# --- Основная логика ---

def run(serial=None):
    print("Начинаем процесс смены аккаунта MLBB...")

    # 1. Авто-определение устройства, если serial не передан
    if serial is None:
        serial = get_device_serial()
        if serial is None:
            print("Ошибка: Устройства не найдены. Запустите эмулятор.")
            return
    
    print(f"Используем устройство: {serial}")

    # Попытка подключения (для инициализации ADB)
    try:
        connect_adb(serial)
    except Exception:
        pass
    
    mlbb_package = "com.mobile.legends"
    
    # 2. Принудительная остановка игры
    print(f"Остановка {mlbb_package}...")
    subprocess.run(['adb', '-s', serial, 'shell', 'am', 'force-stop', mlbb_package], check=True)

    # 3. Переименование папки с кэшем
    original_path = f"/storage/emulated/0/Android/data/{mlbb_package}"
    renamed_path  = f"/storage/emulated/0/Android/data/{mlbb_package}1"
    
    if check_directory_exists_root(serial, renamed_path):
        rename_directory_root(serial, renamed_path, original_path)

    if check_directory_exists_root(serial, original_path):
        rename_directory_root(serial, original_path, renamed_path)
    else:
        print(f"Внимание: Папка {original_path} не найдена.")

    # 4. Сброс данных игры
    clear_app_data(serial, mlbb_package)

    # 5. Сброс Google ID
    reset_google_adid_via_root(serial)

    # 6. Восстановление папки с кэшем
    subprocess.run(['adb', '-s', serial, 'shell', f'rm -rf {original_path}'])
    
    if check_directory_exists_root(serial, renamed_path):
        rename_directory_root(serial, renamed_path, original_path)
    else:
        print("Критическая ошибка: Резервная папка с кэшем пропала!")

    # 7. Запуск игры
    launch_app(serial, mlbb_package)

    print("Готово!")

if __name__ == "__main__":
    run()