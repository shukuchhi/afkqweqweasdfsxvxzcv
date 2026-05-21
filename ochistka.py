"""
Массовая очистка/смена аккаунтов — с защитой от ADB-сбоев.
"""

import sys, os, time, datetime, subprocess, requests
from multiprocessing import Process, Queue

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.adb_helper import adb, restart_adb_server, is_online, get_devices
from modules.change_accounts import run as change_accounts

# ── НАСТРОЙКИ ──────────────────────────────────

LDPLAYER_PATH = r"C:\LDPlayer"
LDPLAYER_EXE  = os.path.join(LDPLAYER_PATH, "dnplayer.exe")
LDCONSOLE_EXE = os.path.join(LDPLAYER_PATH, "dnconsole.exe")

TG_TOKEN  = "8406867386:AAHcfVmPfbV2SfqqDJYO1DI55l3E9GBFyIE"
TG_CHAT_ID = "1767791884"

TIMEOUT          = 300
REBOOT_WAIT_TIME = 120


def send_telegram_alert(serial, script_name, reason_title, error_text=""):
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    message = (
        f"🧹 <b>Mass Cleaner Report {current_time}</b>\n"
        f"📱 <b>Emulator:</b> {serial}\n"
        f"❌ <b>Status:</b> FAILED\n"
        f"⚠️ <b>Reason:</b> {reason_title}\n"
    )
    if error_text:
        clean_error = str(error_text).replace("<", "&lt;").replace(">", "&gt;")
        message += f"🔻 <b>Error:</b>\n<code>{clean_error}</code>"
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      data={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
    except:
        pass


def kill_specific_process(target_index):
    target_str = f"index={target_index}"
    try:
        cmd = 'wmic process where "name=\'dnplayer.exe\'" get processid, commandline'
        output = subprocess.check_output(cmd, shell=True, encoding='cp866', errors='ignore')
        for line in output.strip().split('\n'):
            if target_str in line:
                parts = line.strip().split()
                if parts and parts[-1].isdigit():
                    subprocess.run(f"taskkill /F /PID {parts[-1]}", shell=True,
                                   stdout=subprocess.DEVNULL)
    except:
        pass


def restart_ldplayer(index):
    print(f"[{index}] REBOOTING EMULATOR...")
    try:
        subprocess.run(f'"{LDCONSOLE_EXE}" quit --index {index}', shell=True, timeout=5)
    except:
        pass
    time.sleep(2)
    kill_specific_process(index)
    time.sleep(3)
    subprocess.Popen(f'"{LDPLAYER_EXE}" index={index}', shell=True)


def worker_wrapper(queue, func, serial):
    try:
        func(serial=serial)
    except Exception as e:
        queue.put(str(e))
        sys.exit(1)


def run_task_on_device(serial):
    """Логика для одного устройства: смена аккаунта с ADB-восстановлением."""
    try:
        index = (int(serial.split('-')[1]) - 5554) // 2
    except:
        index = 0

    print(f"\n[{serial}] Запуск очистки аккаунта...")

    error_queue = Queue()
    p = Process(target=worker_wrapper, args=(error_queue, change_accounts, serial))
    p.start()
    p.join(TIMEOUT)

    if p.is_alive():
        print(f"[{serial}] ЗАВИС (TIMEOUT).")
        send_telegram_alert(serial, "Clear Accounts", f"Timeout ({TIMEOUT}s)")
        p.terminate()
        p.join()

        # ═══ ADB-восстановление ═══
        if not is_online(serial):
            restart_adb_server()
            time.sleep(3)
        if not is_online(serial):
            restart_ldplayer(index)
        return

    if p.exitcode != 0:
        print(f"[{serial}] ОШИБКА (CRASH).")
        error_msg = error_queue.get() if not error_queue.empty() else "Unknown"
        reason = "Error"
        if "ADB_TIMEOUT" in error_msg:
            reason = "ADB Timeout"
        elif "ADB_ERROR" in error_msg:
            reason = "ADB Error"

        send_telegram_alert(serial, "Clear Accounts", reason, error_msg)

        # ═══ ADB-восстановление перед ребутом ═══
        if not is_online(serial):
            restart_adb_server()
            time.sleep(3)
        if not is_online(serial):
            restart_ldplayer(index)
        return

    print(f"[{serial}] УСПЕШНО ЗАВЕРШЕНО.")


# ── MAIN ───────────────────────────────────────

if __name__ == "__main__":
    print("=== МАССОВАЯ ОЧИСТКА/СМЕНА АККАУНТОВ ===")
    devices = get_devices()

    if not devices:
        print("Нет подключенных устройств! Запустите эмуляторы.")
        sys.exit()

    print(f"Найдено устройств: {len(devices)} -> {devices}")

    active_processes = []
    for serial in devices:
        p = Process(target=run_task_on_device, args=(serial,))
        p.start()
        active_processes.append(p)

    for p in active_processes:
        p.join()

    print("\n=== ГОТОВО ===")