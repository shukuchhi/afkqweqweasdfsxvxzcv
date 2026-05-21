import sys
import os
import json
import argparse
import time
import datetime
import subprocess
import requests
from multiprocessing import Process, Queue

# ==============================================================================
#                               НАСТРОЙКИ (CONFIG)
# ==============================================================================

LDPLAYER_PATH = r"D:\LDPlayer\LDPlayer14"
LDPLAYER_EXE = os.path.join(LDPLAYER_PATH, "dnplayer.exe")
LDCONSOLE_EXE = os.path.join(LDPLAYER_PATH, "dnconsole.exe")
BOT_CONFIG_PATH = r"C:\Users\shukuchhi\Documents\425\config.json"
BOT_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "bot_settings.json")
DEFAULT_SERIAL = "emulator-5558"

# Настройки Telegram
TG_TOKEN = "8406867386:AAHcfVmPfbV2SfqqDJYO1DI55l3E9GBFyIE"
TG_CHAT_ID = "1767791884"

# Таймауты
TIMEOUT_CHANGE_ACCOUNTS = 300
TIMEOUT_GAME_BOTS = 900
TIMEOUT_DEFAULT = 600
TIMEOUT_EMAIL_VERIFICATION = 600
REBOOT_WAIT_TIME = 120

# ==============================================================================

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))

from modules.account_creation import run as accountcreation
from modules.gamebot1 import run as game1
from modules.collect1 import run as collect1
from modules.gamebot2 import run as game2
from modules.gamebot1_5 import run as game4
from modules.collect2 import run as collect2
from modules.collect3 import run as collect3
from modules.collect4 import run as collect4
from modules.collect5_1 import run as collect5
from modules.collect6 import run as collect6
from modules.collect8 import run as collect8
from modules.email_verification import run as email_verification
from modules.emain_verification_vilet import run as email_recovery
from modules.change_accounts import run as change_accounts
from modules.email_verification200 import run as email_verification200

# ==============================================================================
#                          НАСТРОЙКИ ВОПРОСОВ
# ==============================================================================
#
#   Чтобы добавить свой вопрос:
#   1. Придумай ключ (например "my_setting")
#   2. Напиши вопрос в "question"
#   3. Добавь варианты ответов в "options"
#      "1": {"label": "Описание", "value": значение}
#   Пример добавлен внизу в комментарии
#
# ==============================================================================

QUESTIONS = {
    "tickets_count": {
        "question": "На аккаунте сколько билетов?",
        "options": {
            "1": {"label": "0 билетов",   "value": 0},
            "2": {"label": "200 билетов", "value": 200},
        }
    },

    # --- ДОБАВЛЯЙ СВОИ ВОПРОСЫ НИЖЕ ---
    # "my_setting": {
    #     "question": "Твой вопрос здесь?",
    #     "options": {
    #         "1": {"label": "Вариант А", "value": "a"},
    #         "2": {"label": "Вариант Б", "value": "b"},
    #     }
    # },
}


# ==============================================================================
#                        РАБОТА С НАСТРОЙКАМИ (JSON)
# ==============================================================================

def load_bot_settings() -> dict:
    """Загружает настройки из bot_settings.json"""
    if not os.path.exists(BOT_SETTINGS_PATH):
        print(f"[WARN] Файл настроек не найден: {BOT_SETTINGS_PATH}")
        print("[WARN] Используем значение по умолчанию: 0 билетов")
        return {}
    try:
        with open(BOT_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Ошибка чтения настроек: {e}")
        return {}


def save_bot_settings(settings: dict):
    """Сохраняет настройки в bot_settings.json"""
    with open(BOT_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)
    print(f"\n✅ Настройки сохранены в '{BOT_SETTINGS_PATH}'")


def ask_and_save_settings():
    """
    Задаёт все вопросы из QUESTIONS пользователю
    и сохраняет ответы в bot_settings.json
    """
    print("\n" + "=" * 50)
    print("          НАСТРОЙКА БОТА")
    print("=" * 50)

    settings = load_bot_settings()

    for key, data in QUESTIONS.items():
        print(f"\n❓ {data['question']}")

        # Показываем варианты
        for num, option in data["options"].items():
            print(f"   {num} - {option['label']}")

        # Показываем текущее значение если есть
        if key in settings:
            print(f"   (Текущее значение: {settings[key]} | Enter = оставить)")

        # Читаем ввод
        while True:
            user_input = input("   Твой выбор: ").strip()

            # Если пусто и есть текущее — оставляем старое
            if user_input == "" and key in settings:
                print(f"   ↩️  Оставлено: {settings[key]}")
                break

            if user_input in data["options"]:
                chosen_value = data["options"][user_input]["value"]
                settings[key] = chosen_value
                print(f"   ✔️  Выбрано: {data['options'][user_input]['label']}")
                break
            else:
                valid = ", ".join(data["options"].keys())
                print(f"   ⚠️  Неверный ввод. Введи одно из: {valid}")

    save_bot_settings(settings)

    print("\n📋 Итоговые настройки:")
    print(json.dumps(settings, ensure_ascii=False, indent=4))

    return settings


def get_email_verification_func() -> tuple:
    """
    Возвращает (функция, название) верификации
    в зависимости от количества билетов в настройках.

    0 билетов   -> email_verification
    200 билетов -> email_verification200
    """
    settings = load_bot_settings()
    tickets = settings.get("tickets_count", 0)

    print(f"[SETTINGS] Билетов на аккаунте: {tickets}")

    if tickets == 200:
        print("[SETTINGS] Используем: email_verification200")
        return email_verification200, "Email Verification 200"
    else:
        print("[SETTINGS] Используем: email_verification (стандарт)")
        return email_verification, "Email Verification"


# ==============================================================================
#                             TELEGRAM
# ==============================================================================

def send_telegram_alert(serial, script_name, reason_title, error_text="", custom_header=None):
    """
    Отправляет уведомление в Telegram.
    custom_header: Заменяет стандартный заголовок (для красивых уведомлений).
    """
    current_time = datetime.datetime.now().strftime("%H:%M:%S")

    if custom_header:
        header = f"{custom_header} {current_time}"
    else:
        header = f"⚠️ <b>Сбой {current_time}</b>"

    message = (
        f"{header}\n"
        f"📱 <b>Номер эмулятора:</b> {serial}\n"
        f"📜 <b>Скрипт:</b> {script_name}\n"
        f"❌ <b>Причина:</b> {reason_title}\n"
    )

    if error_text:
        clean_error = str(error_text).replace("<", "&lt;").replace(">", "&gt;")
        message += f"🔻 <b>Текст ошибки:</b>\n<code>{clean_error}</code>"

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"[TG ERROR] Не удалось отправить сообщение: {e}")


# ==============================================================================
#                          УПРАВЛЕНИЕ ЭМУЛЯТОРОМ
# ==============================================================================

def kill_specific_process(target_index):
    target_str = f"index={target_index}"
    print(f"[KILLER] Поиск процесса '{target_str}'...")
    try:
        cmd = 'wmic process where "name=\'dnplayer.exe\'" get processid, commandline'
        output = subprocess.check_output(cmd, shell=True, encoding='cp866', errors='ignore')
        lines = output.strip().split('\n')
        for line in lines:
            if target_str in line:
                parts = line.strip().split()
                if parts:
                    pid = parts[-1]
                    if pid.isdigit():
                        print(f"[KILLER] Убиваем PID: {pid}")
                        subprocess.run(
                            f"taskkill /F /PID {pid}",
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
    except Exception as e:
        print(f"[KILLER ERROR] {e}")


def restart_ldplayer(index=0):
    print(f"\n[SYSTEM] >>> ПЕРЕЗАГРУЗКА ЭМУЛЯТОРА (INDEX: {index}) <<<")
    try:
        subprocess.run(f'"{LDCONSOLE_EXE}" quit --index {index}', shell=True, timeout=5)
    except:
        pass
    time.sleep(2)
    kill_specific_process(index)
    time.sleep(3)
    cmd = f'"{LDPLAYER_EXE}" index={index}'
    print(f"[SYSTEM] Запуск: {cmd}")
    try:
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        print(f"[ERROR] Не удалось запустить: {e}")
    print(f"[SYSTEM] Ждем загрузку ({REBOOT_WAIT_TIME} сек)...")
    time.sleep(REBOOT_WAIT_TIME)
    print("[SYSTEM] Готово.")



# ==============================================================================
#                        ЗАПУСК СКРИПТОВ В ПРОЦЕССАХ
# ==============================================================================

def worker_wrapper(queue, func, serial):
    try:
        func(serial=serial)
    except Exception as e:
        queue.put(str(e))
        sys.exit(1)


def run_script_safe(script_func, script_name, serial, timeout, mute_alerts=False):
    """
    Запускает скрипт в отдельном процессе с таймаутом.
    mute_alerts=True: не отправлять '⚠️ Сбой' автоматически.
    Возвращает True если успешно, False если таймаут или ошибка.
    """
    error_queue = Queue()
    p = Process(target=worker_wrapper, args=(error_queue, script_func, serial))
    p.start()
    p.join(timeout)

    # 1. ТАЙМАУТ
    if p.is_alive():
        print(f"\n[TIMEOUT] Скрипт '{script_name}' завис.")
        if not mute_alerts:
            send_telegram_alert(serial, script_name, f"Просрочил время ({timeout} сек)")
        p.terminate()
        p.join()
        return False

    # 2. ОШИБКА
    if p.exitcode != 0:
        print(f"\n[CRASH] Скрипт '{script_name}' упал.")
        error_msg = "Unknown Error"
        if not error_queue.empty():
            error_msg = error_queue.get()
        print(f"Текст ошибки: {error_msg}")

        reason = "Скрипт прислал ошибку"
        if "ADB_TIMEOUT" in error_msg:
            reason = "ADB Timeout!"
        elif "ADB_ERROR" in error_msg:
            reason = "ADB Error!"

        if not mute_alerts:
            send_telegram_alert(serial, script_name, reason, error_msg)
        return False

    return True


# ==============================================================================
#                               ГЛАВНЫЙ ЦИКЛ
# ==============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', type=str, default=DEFAULT_SERIAL)
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Запустить настройку и сохранить в bot_settings.json'
    )
    args = parser.parse_args()

    if args.setup:
        ask_and_save_settings()
        return

    emulator_index = 0
    try:
        port = int(args.serial.split('-')[1])
        emulator_index = (port - 5554) // 2
    except:
        pass

    print(f"\n=== ЗАПУСК БОТА {args.serial} (Index: {emulator_index}) ===")

    try:
        with open(BOT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"[FATAL] Ошибка конфига: {e}")
        return

    current_settings = load_bot_settings()
    print(f"[SETTINGS] Текущие настройки: {json.dumps(current_settings, ensure_ascii=False)}")

    # Список задач БЕЗ Account Creation (он обрабатывается отдельно)
    pre_email_scripts = [
        ("Game 1 AFK Bot",   game1),
        ("Collect 1",        collect1),
        ("Game 2 AFK Bot",   game4),
        ("Collect 2",        collect2),
        ("Game 2 AFK Bot",   game2),
        ("Collect 3",        collect3),
        ("Game 2 AFK Bot",   game2),
        ("Collect 4",        collect4),
        ("Game 2 AFK Bot",   game2),
        ("Collect 5",        collect5),
        ("Game 2 AFK Bot",   game2),
        ("Collect 5",        collect6),
        ("Game 2 AFK Bot",   game2),
        ("Collect 5",        collect6),
        ("Game 2 AFK Bot",   game2),
        ("Collect 8",        collect8),
    ]

    cycle_count = 0
    while True:
        cycle_count += 1
        print(f"\n>>> ЦИКЛ {cycle_count} <<<")
        restart_cycle_needed = False

        # ------------------------------------------------------------------
        # 1a. ACCOUNT CREATION (особая обработка сбоя)
        #     Если падает -> TG уведомление (штатное) + change_accounts
        #     Без перезапуска эмулятора!
        # ------------------------------------------------------------------
        print(f"\n[RUN] Account Creation (Max: {TIMEOUT_DEFAULT}s)...")
        success = run_script_safe(
            accountcreation, "Account Creation",
            args.serial, TIMEOUT_DEFAULT
        )

        if not success:
            print("[FAIL] Сбой в Account Creation.")
            print("[RECOVERY] Запускаем смену аккаунта (без перезапуска эмулятора)...")

            run_script_safe(
                change_accounts, "Emergency Change (Account Creation)",
                args.serial, TIMEOUT_CHANGE_ACCOUNTS
            )

            print("[RECOVERY] Рестарт цикла.")
            continue  # <-- просто идём на следующий цикл

        time.sleep(2)

        # ------------------------------------------------------------------
        # 1b. ОСТАЛЬНЫЕ СКРИПТЫ (стандартная обработка сбоя)
        # ------------------------------------------------------------------
        for script_name, script_func in pre_email_scripts:

            if "Game" in script_name:
                timeout = TIMEOUT_GAME_BOTS
            else:
                timeout = TIMEOUT_DEFAULT

            print(f"\n[RUN] {script_name} (Max: {timeout}s)...")
            success = run_script_safe(script_func, script_name, args.serial, timeout)

            if not success:
                print(f"[FAIL] Сбой в {script_name}. Восстановление...")
                restart_ldplayer(emulator_index)

                print("[RECOVERY] Аварийная смена аккаунта...")
                run_script_safe(
                    change_accounts, "Emergency Change",
                    args.serial, TIMEOUT_CHANGE_ACCOUNTS
                )

                print("[RECOVERY] Рестарт цикла.")
                restart_cycle_needed = True
                break

            time.sleep(2)

        if restart_cycle_needed:
            continue

        # ------------------------------------------------------------------
        # 2. ВЕРИФИКАЦИЯ ПОЧТЫ
        # ------------------------------------------------------------------
        ev_func, ev_name = get_email_verification_func()
        print(f"\n[RUN] {ev_name}...")

        if run_script_safe(ev_func, ev_name, args.serial, TIMEOUT_EMAIL_VERIFICATION):
            print("[OK] Email confirmed.")
        else:
            print("[WARN] Основная верификация не удалась. Запуск прослойки...")

            recovery_success = False
            max_tries = 2

            for i in range(1, max_tries + 1):
                header_text = f"🔄 <b>Попытка восстановления {i}/{max_tries}</b>"
                send_telegram_alert(
                    args.serial, "Email Recovery",
                    "Пробуем через vilet...",
                    custom_header=header_text
                )

                restart_ldplayer(emulator_index)

                if run_script_safe(
                    email_recovery, f"Email Recovery #{i}",
                    args.serial, TIMEOUT_EMAIL_VERIFICATION,
                    mute_alerts=True
                ):
                    header_text = "✅ <b>ПОЧИНИЛИ!</b>"
                    send_telegram_alert(
                        args.serial, "Email Recovery",
                        "Сработало!",
                        custom_header=header_text
                    )
                    recovery_success = True
                    break
                else:
                    header_text = f"⚠️ <b>Неудача {i}/{max_tries}</b>"
                    send_telegram_alert(
                        args.serial, f"Email Recovery #{i}",
                        "Скрипт упал",
                        custom_header=header_text
                    )

            if not recovery_success:
                print("[FATAL] Восстановление не удалось.")
                send_telegram_alert(
                    args.serial, "Email Verification FATAL",
                    "Все попытки (2/2) провалены. Создаем новый аккаунт."
                )
                restart_ldplayer(emulator_index)
                run_script_safe(
                    change_accounts, "Failed Acc Change",
                    args.serial, TIMEOUT_CHANGE_ACCOUNTS
                )
                continue

        # ------------------------------------------------------------------
        # 3. СМЕНА АККАУНТА (ФИНАЛ)
        # ------------------------------------------------------------------
        print(f"\n[RUN] Change Accounts...")
        success = run_script_safe(
            change_accounts, "Change Accounts",
            args.serial, TIMEOUT_CHANGE_ACCOUNTS
        )

        if not success:
            restart_ldplayer(emulator_index)

        print(f"\n>>> ЦИКЛ {cycle_count} ЗАВЕРШЕН <<<")
        time.sleep(10)


if __name__ == "__main__":
    main()