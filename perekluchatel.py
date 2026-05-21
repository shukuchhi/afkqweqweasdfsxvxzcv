import ctypes
import sys
import os
import psutil
import time
import keyboard
from ctypes import wintypes

# ─────────────────────────────────────────────
#  САМО-ПЕРЕЗАПУСК ОТ АДМИНА
# ─────────────────────────────────────────────
def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def relaunch_as_admin():
    script = os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
    sys.exit(0)

if not is_admin():
    relaunch_as_admin()

# ─────────────────────────────────────────────
#  КОНСТАНТЫ И СТРУКТУРЫ
# ─────────────────────────────────────────────
TARGET_PROCESS = "ld9boxheadless.exe"
CHECK_INTERVAL_SEC = 20

# Права доступа: информация о процессе + установка информации
PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
IDLE_PRIORITY_CLASS = 0x00000040

# Константы для Efficiency Mode
ProcessPowerThrottling = 18
PROCESS_POWER_THROTTLING_CURRENT_VERSION = 1
PROCESS_POWER_THROTTLING_EXECUTION_SPEED = 0x1

class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
    _fields_ = [
        ("Version", wintypes.ULONG),
        ("ControlMask", wintypes.ULONG),
        ("StateMask", wintypes.ULONG),
    ]

# ─────────────────────────────────────────────
#  ФУНКЦИЯ УСТАНОВКИ РЕЖИМА
# ─────────────────────────────────────────────
def set_efficiency_mode(pid: int) -> str:
    """
    Пытается включить Efficiency Mode и Idle Priority.
    Возвращает текстовый статус.
    """
    try:
        # Открываем процесс с расширенными правами
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION, 
            False, pid
        )
        
        if not handle:
            return f"Ошибка доступа (WinError {ctypes.windll.kernel32.GetLastError()})"

        results = []

        # 1. Попытка установить Низкий приоритет (IDLE)
        if ctypes.windll.kernel32.SetPriorityClass(handle, IDLE_PRIORITY_CLASS):
            results.append("Приоритет: Низкий")
        else:
            results.append(f"Приоритет: Ошибка {ctypes.windll.kernel32.GetLastError()}")

        # 2. Попытка включить Efficiency Mode (EcoQoS)
        throttle = PROCESS_POWER_THROTTLING_STATE(
            Version = PROCESS_POWER_THROTTLING_CURRENT_VERSION,
            ControlMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED,
            StateMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED,
        )
        
        res = ctypes.windll.kernel32.SetProcessInformation(
            handle,
            ProcessPowerThrottling,
            ctypes.byref(throttle),
            ctypes.sizeof(throttle),
        )

        if res:
            results.append("EcoQoS: ВКЛ")
        else:
            err = ctypes.windll.kernel32.GetLastError()
            if err == 87:
                results.append("EcoQoS: Не поддерживается процессом (Error 87)")
            else:
                results.append(f"EcoQoS: Ошибка {err}")

        ctypes.windll.kernel32.CloseHandle(handle)
        return " | ".join(results)

    except Exception as e:
        return f"Критическая ошибка: {e}"

# ─────────────────────────────────────────────
#  ОСНОВНОЙ ЦИКЛ
# ─────────────────────────────────────────────
applied_pids = set()
stop_flag = False

def stop():
    global stop_flag
    stop_flag = True
    print("\n[СТОП] Завершаю работу...")

keyboard.add_hotkey("f10", stop)

def main():
    print("=" * 60)
    print("  EcoQoS & Priority Manager")
    print(f"  Цель: {TARGET_PROCESS}")
    print("  F10 — остановить работу")
    print("=" * 60)

    while not stop_flag:
        # Очистка мертвых PID
        dead = {pid for pid in applied_pids if not psutil.pid_exists(pid)}
        applied_pids.difference_update(dead)

        found_any = False
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"].lower() == TARGET_PROCESS.lower():
                    pid = proc.info["pid"]
                    if pid not in applied_pids:
                        status = set_efficiency_mode(pid)
                        print(f"[PID {pid}] {status}")
                        applied_pids.add(pid)
                    found_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not found_any:
            print("...ожидание процессов...", end="\r")

        # Пауза с проверкой флага остановки
        for _ in range(CHECK_INTERVAL_SEC * 2):
            if stop_flag: break
            time.sleep(0.5)

if __name__ == "__main__":
    main()