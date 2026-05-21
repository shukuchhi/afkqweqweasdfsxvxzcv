"""
Смена аккаунта MLBB: force-stop → переименование кэша → pm clear → сброс Google ID → запуск.
Все ADB-вызовы через adb_helper.adb() — защита от kill-server.
"""

import sys, os, time, subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.adb_helper import check_adb_devices

from utils.adb_helper import adb, get_devices
from utils.adb_utils import connect_adb


def get_device_serial():
    """Авто-определение serial первого устройства."""
    devs = get_devices()
    return devs[0] if devs else None


# ── ХЕЛПЕРЫ (все через adb_helper) ─────────────

def _shell(serial: str, cmd: str):
    """Выполнить shell-команду с защитой."""
    adb(serial, 'shell', cmd)


def check_directory_exists_root(serial, path):
    r = subprocess.run(
        ['adb', '-s', serial, 'shell', f'su -c "ls -d {path}"'],
        capture_output=True, text=True,
    )
    return path in r.stdout


def reset_google_adid_via_root(serial):
    print("Сброс Google Advertising ID...")
    target = "/data/data/com.google.android.gms/shared_prefs/adid_settings.xml"
    try:
        _shell(serial, f'su -c "rm -f {target}"')
        print("Google ID сброшен.")
        return True
    except RuntimeError:
        print("Не удалось сбросить ID (возможно нет Root прав).")
        return False


def rename_directory_root(serial, old_path, new_path):
    print(f"Переименование: {old_path} -> {new_path}")
    try:
        _shell(serial, f'su -c "mv {old_path} {new_path}"')
        return True
    except RuntimeError:
        return False


def clear_app_data(serial, package_name):
    print(f"Быстрая очистка данных {package_name}...")
    try:
        _shell(serial, f'pm clear {package_name}')
        print("Данные очищены.")
    except RuntimeError as e:
        print(f"Ошибка очистки: {e}")


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
    raise RuntimeError(
        f"ADB_ERROR: Не удалось определить Activity для {package_name}.\nВывод: {result.stdout!r}"
    )


def launch_app(serial, package_name):
    print(f"Запуск {package_name}...")
    component = _get_main_activity(serial, package_name)
    print(f"[DEBUG] Запускаем компонент: {component}")
    try:
        _shell(serial, f'am start -n {component}')
    except RuntimeError as e:
        raise RuntimeError(f"ADB_ERROR: Не удалось запустить {package_name}.\n{e}")
    print("Готово!")


# ── ОСНОВНАЯ ЛОГИКА ────────────────────────────

def run(serial=None):
    print("Начинаем процесс смены аккаунта MLBB...")

    if serial is None:
        serial = get_device_serial()
        if serial is None:
            print("Ошибка: Устройства не найдены. Запустите эмулятор.")
            return

    print(f"Используем устройство: {serial}")

    try:
        connect_adb(serial)
    except Exception:
        pass

    mlbb = "com.mobile.legends"

    # 1. Остановка
    print(f"Остановка {mlbb}...")
    _shell(serial, f'am force-stop {mlbb}')

    # 2. Кэш
    original = f"/storage/emulated/0/Android/data/{mlbb}"
    renamed  = f"/storage/emulated/0/Android/data/{mlbb}1"

    if check_directory_exists_root(serial, renamed):
        rename_directory_root(serial, renamed, original)

    if check_directory_exists_root(serial, original):
        rename_directory_root(serial, original, renamed)
    else:
        print(f"Внимание: Папка {original} не найдена.")

    # 3. Очистка данных
    clear_app_data(serial, mlbb)

    # 4. Google ID
    reset_google_adid_via_root(serial)

    # 5. Восстановление кэша
    _shell(serial, f'rm -rf {original}')
    if check_directory_exists_root(serial, renamed):
        rename_directory_root(serial, renamed, original)
    else:
        print("Критическая ошибка: Резервная папка с кэшем пропала!")

    # 6. Запуск
    launch_app(serial, mlbb)
    print("Готово!")


if __name__ == "__main__":
    run()