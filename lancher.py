# launcher.py
import subprocess
import time
import sys
import os
import ctypes


# ─────────────────────────────────────────────
#  ADB
# ─────────────────────────────────────────────
def get_connected_devices():
    """Получает список подключенных устройств через ADB."""
    print("\n[ADB] Поиск устройств...")
    try:
        subprocess.run(
            "adb start-server",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        output = subprocess.check_output(
            "adb devices", shell=True
        ).decode("utf-8")

        lines = output.strip().split("\n")[1:]
        devices = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices

    except Exception as e:
        print(f"[ADB] Ошибка: {e}")
        return []


# ─────────────────────────────────────────────
#  ЗАПУСК perekluchatel.py ЧЕРЕЗ UAC (руnas)
# ─────────────────────────────────────────────
def launch_perekluchatel_as_admin(script_path: str, python_exe: str):
    """
    Запускает perekluchatel.py с правами администратора через UAC.
    Окно cmd остаётся открытым (/k) — видны логи.
    """
    if not os.path.exists(script_path):
        print(f"[WARN] Файл {script_path} не найден, пропускаем.")
        return

    print("[UAC] Запрашиваю права для perekluchatel.py...")

    # cmd.exe запускаем от админа, он уже открывает питон внутри себя
    # Так окно остаётся видимым и с правами администратора
    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",                        # запрос UAC
        "cmd.exe",                      # что запускаем
        f'/k ""{python_exe}" "{script_path}""',  # аргументы cmd
        None,
        1                               # SW_SHOWNORMAL
    )

    if result <= 32:
        print(f"[ОШИБКА] Не удалось запустить perekluchatel.py (код {result}).")
        print("         UAC отклонён или произошла ошибка.")
    else:
        print("[✓] perekluchatel.py запущен с правами администратора.")


# ─────────────────────────────────────────────
#  ГЛАВНАЯ ЛОГИКА
# ─────────────────────────────────────────────
def main():
    print("========================================")
    print("       MULTI-INSTANCE BOT LAUNCHER      ")
    print("========================================")

    # ── Пути ────────────────────────────────────
    current_dir  = os.path.dirname(os.path.abspath(__file__))
    main_script  = os.path.join(current_dir, "main.py")
    final_script = os.path.join(current_dir, "perekluchatel.py")
    python_exe   = sys.executable

    # ── Проверка main.py ────────────────────────
    if not os.path.exists(main_script):
        print(f"\n[ОШИБКА] Файл {main_script} не найден!")
        input("Нажмите Enter для выхода...")
        return

    # ── Поиск эмуляторов ────────────────────────
    devices = get_connected_devices()

    if not devices:
        print("\n[!] Эмуляторы не найдены в ADB.")
        print("    Убедитесь, что LDPlayer запущен.")
        input("\nНажмите Enter для выхода...")
        return

    print(f"\n[✓] Найдено активных эмуляторов: {len(devices)}")
    print("    Запуск процессов...\n")
    time.sleep(1)

    # ── Запуск ботов (обычные права) ────────────
    for serial in devices:
        cmd = (
            f'start "Bot-{serial}" cmd /k '
            f'""{python_exe}" "{main_script}" --serial {serial}""'
        )
        print(f"  -> Запуск бота: {serial}")
        subprocess.Popen(cmd, shell=True)
        time.sleep(60)  # пауза между запусками

    # ── Запуск perekluchatel.py ЧЕРЕЗ UAC ───────
    print()
    launch_perekluchatel_as_admin(final_script, python_exe)

    # ── Финал ───────────────────────────────────
    print("\n[ГОТОВО] Все задачи запущены.")
    print("Лаунчер закрывается через 2 секунды...")
    time.sleep(2)
    sys.exit()


if __name__ == "__main__":
    main()