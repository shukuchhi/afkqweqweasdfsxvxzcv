"""
perekluchatel.py — EcoQoS + расстановка окон LDPlayer + переключение

Ширина монитора читается автоматически через GetSystemMetrics.
Окна делятся горизонтально поровну, Y и высота не трогаются.
Клик всегда по: left + OFFSET_X, top + OFFSET_Y

Alt  — пауза / продолжить
F10  — остановить
"""

import ctypes
import ctypes.wintypes as wt
import sys
import os
import time
import psutil
import keyboard

# ─────────────────────────────────────────────
# САМО-ПЕРЕЗАПУСК ОТ АДМИНА
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
# WIN32
# ─────────────────────────────────────────────
kernel32 = ctypes.windll.kernel32
user32   = ctypes.windll.user32

kernel32.SetProcessInformation.restype  = wt.BOOL
kernel32.SetProcessInformation.argtypes = [
    wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD,
]
kernel32.GetProcessInformation.restype  = wt.BOOL
kernel32.GetProcessInformation.argtypes = [
    wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD,
]

# ─────────────────────────────────────────────
# НАСТРОЙКИ
# ─────────────────────────────────────────────
TARGET_PROCESS      = "ld9boxheadless.exe"
WINDOW_PROCESS      = "dnplayer.exe"

# Ширина монитора — читается автоматически
# SM_CXSCREEN=0 → реальные пиксели (для 4K без DPI scaling даёт 3840)
# Если у тебя DPI scaling 150%+, раскомментируй строку с GetSystemMetricsForDpi
SCREEN_WIDTH: int   = user32.GetSystemMetrics(0)

OFFSET_X            = 220    # смещение клика от левого края окна
OFFSET_Y            = 20     # смещение клика от верхнего края окна

CHECK_INTERVAL      = 30     # секунд между проверками EcoQoS и расстановки
WINDOW_SWITCH_DELAY = 3     # секунд между переключениями окон

TOLERANCE           = 5      # пикселей — допуск позиционирования

# ─────────────────────────────────────────────
# WIN32 КОНСТАНТЫ
# ─────────────────────────────────────────────
PROCESS_SET_INFORMATION           = 0x0200
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
IDLE_PRIORITY_CLASS               = 0x00000040

ProcessPowerThrottling                   = 4
PROCESS_POWER_THROTTLING_VERSION_1       = 1
PROCESS_POWER_THROTTLING_EXECUTION_SPEED = 0x1

SWP_NOACTIVATE = 0x0010
SWP_NOZORDER   = 0x0004
SW_RESTORE     = 9


class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
    _fields_ = [
        ("Version",     ctypes.c_ulong),
        ("ControlMask", ctypes.c_ulong),
        ("StateMask",   ctypes.c_ulong),
    ]


# ─────────────────────────────────────────────
# EcoQoS
# ─────────────────────────────────────────────
def open_process(pid: int) -> wt.HANDLE:
    handle = kernel32.OpenProcess(
        PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION,
        False, pid
    )
    if not handle:
        raise PermissionError(f"OpenProcess failed pid={pid} err={kernel32.GetLastError()}")
    return handle


def set_eco_mode(pid: int) -> str:
    try:
        handle = open_process(pid)
    except PermissionError as e:
        return f"❌ {e}"

    results = []
    try:
        if kernel32.SetPriorityClass(handle, IDLE_PRIORITY_CLASS):
            results.append("Priority:Idle✓")
        else:
            results.append(f"Priority:err{kernel32.GetLastError()}")

        t    = PROCESS_POWER_THROTTLING_STATE(
            Version     = PROCESS_POWER_THROTTLING_VERSION_1,
            ControlMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED,
            StateMask   = PROCESS_POWER_THROTTLING_EXECUTION_SPEED,
        )
        ptr  = ctypes.cast(ctypes.byref(t), ctypes.c_void_p)
        size = wt.DWORD(ctypes.sizeof(t))
        ok   = kernel32.SetProcessInformation(handle, ProcessPowerThrottling, ptr, size)
        if ok:
            results.append("EcoQoS✓")
        else:
            err = kernel32.GetLastError()
            results.append("EcoQoS:н/д" if err == 87 else f"EcoQoS:err{err}")
    finally:
        kernel32.CloseHandle(handle)

    return " | ".join(results)


def check_eco_mode(pid: int) -> bool:
    try:
        handle = open_process(pid)
    except PermissionError:
        return False
    try:
        t    = PROCESS_POWER_THROTTLING_STATE()
        ptr  = ctypes.cast(ctypes.byref(t), ctypes.c_void_p)
        size = wt.DWORD(ctypes.sizeof(t))
        ok   = kernel32.GetProcessInformation(handle, ProcessPowerThrottling, ptr, size)
        if not ok:
            return False
        return bool(
            t.ControlMask & PROCESS_POWER_THROTTLING_EXECUTION_SPEED and
            t.StateMask   & PROCESS_POWER_THROTTLING_EXECUTION_SPEED
        )
    finally:
        kernel32.CloseHandle(handle)


# ─────────────────────────────────────────────
# ОКНА — получение
# ─────────────────────────────────────────────
def get_ldplayer_windows() -> list:
    """Список (hwnd, pid, title), отсортированный по текущей X-позиции."""
    windows = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            proc = psutil.Process(pid.value)
            if proc.name().lower() == WINDOW_PROCESS.lower():
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                windows.append((hwnd, pid.value, buf.value))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)

    def get_x(item):
        rect = wt.RECT()
        user32.GetWindowRect(item[0], ctypes.byref(rect))
        return rect.left

    windows.sort(key=get_x)
    return windows


# ─────────────────────────────────────────────
# ОКНА — расстановка
# ─────────────────────────────────────────────
def arrange_windows(windows: list):
    """
    Делит актуальную ширину монитора на количество окон,
    расставляет их горизонтально в ряд слева направо.
    Y и высота — не трогаются.
    """
    count = len(windows)
    if count == 0:
        return

    # Перечитываем ширину монитора каждый раз — вдруг изменилась
    screen_w = user32.GetSystemMetrics(0)
    slot_w   = screen_w // count
    changed  = 0

    print(f"  [LAYOUT] Монитор: {screen_w}px | окон: {count} | слот: {slot_w}px")

    for i, (hwnd, pid, title) in enumerate(windows):
        target_x = i * slot_w
        target_y = 0
        target_w = slot_w

        rect = wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        cur_x = rect.left
        cur_w = rect.right - rect.left
        cur_y = rect.top
        cur_h = rect.bottom - rect.top

        needs_move   = abs(cur_x - target_x) > TOLERANCE or abs(cur_y - target_y) > TOLERANCE
        needs_resize = abs(cur_w - target_w) > TOLERANCE

        if needs_move or needs_resize:
            user32.ShowWindow(hwnd, SW_RESTORE)
            time.sleep(0.05)

            user32.SetWindowPos(
                hwnd,
                None,
                target_x,   # X
                target_y,   # Y = 0 (всегда сверху)
                target_w,    # ширина
                cur_h,       # высота — не трогаем
                SWP_NOACTIVATE | SWP_NOZORDER,
            )
            changed += 1
            print(f"  [LAYOUT] '{title}' → x={target_x} y={target_y} w={target_w}  (было x={cur_x} y={cur_y} w={cur_w})")

    if changed == 0:
        print(f"  [LAYOUT] Все окна стоят правильно")
    else:
        print(f"  [LAYOUT] Переставлено: {changed}/{count}")


# ─────────────────────────────────────────────
# ПЕРЕКЛЮЧЕНИЕ + КЛИК
# ─────────────────────────────────────────────
def bring_window_and_click(hwnd: int, title: str):
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)

    rect = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    x = rect.left + OFFSET_X
    y = rect.top  + OFFSET_Y

    user32.SetCursorPos(x, y)
    time.sleep(0.1)
    user32.mouse_event(0x0002, 0, 0, 0, 0)   # LEFTDOWN
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)   # LEFTUP

    print(f"  [КЛИК] '{title}' → ({x},{y})")


# ─────────────────────────────────────────────
# СОСТОЯНИЕ
# ─────────────────────────────────────────────
applied_pids: set = set()
paused:       bool = False
stop_flag:    bool = False


def toggle_pause():
    global paused
    paused = not paused
    print(f"\n[ALT] {'⏸ ПАУЗА' if paused else '▶ РАБОТАЕТ'}\n")


def stop_script():
    global stop_flag
    stop_flag = True
    print("\n[F10] Завершаю работу...")


keyboard.add_hotkey("alt", toggle_pause)
keyboard.add_hotkey("f10", stop_script)


# ─────────────────────────────────────────────
# EcoQoS: сканирование
# ─────────────────────────────────────────────
def scan_and_apply_eco():
    dead = {pid for pid in applied_pids if not psutil.pid_exists(pid)}
    if dead:
        applied_pids.difference_update(dead)
        print(f"  [ECO] Мёртвых убрано: {len(dead)}")

    found = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"].lower() == TARGET_PROCESS.lower():
                found.append(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not found:
        print("  [ECO] Процессов не найдено")
        return

    new_ok = reapplied = errors = 0

    for pid in found:
        if pid not in applied_pids:
            status = set_eco_mode(pid)
            print(f"  [ECO] PID {pid} (новый): {status}")
            if "❌" in status:
                errors += 1
            else:
                applied_pids.add(pid)
                new_ok += 1
        else:
            if not check_eco_mode(pid):
                print(f"  [ECO] PID {pid} — слетел, перевешиваю...")
                status = set_eco_mode(pid)
                print(f"         → {status}")
                if "❌" in status:
                    applied_pids.discard(pid)
                    errors += 1
                else:
                    reapplied += 1

    print(f"  [ECO] Всего: {len(found)} | новых: {new_ok} | перевешено: {reapplied} | ошибок: {errors}")


# ─────────────────────────────────────────────
# ГЛАВНЫЙ ЦИКЛ
# ─────────────────────────────────────────────
def main():
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)

    print("=" * 60)
    print("  LDPlayer Manager  —  EcoQoS + Layout + Switcher")
    print(f"  EcoQoS цель  : {TARGET_PROCESS}")
    print(f"  Окна цель    : {WINDOW_PROCESS}")
    print(f"  Монитор      : {screen_w}×{screen_h}px (авто)")
    print(f"  Клик         : left+{OFFSET_X}, top+{OFFSET_Y}")
    print(f"  Проверка     : каждые {CHECK_INTERVAL}с")
    print(f"  Переключение : каждые {WINDOW_SWITCH_DELAY}с")
    print("  Alt  — пауза / продолжить")
    print("  F10  — остановить")
    print("=" * 60)
    print()

    last_check = 0

    while not stop_flag:

        if paused:
            print("  ⏸ Пауза... (Alt — снять)", end="\r")
            time.sleep(0.5)
            continue

        now = time.time()

        # ── Плановая проверка ──────────────────────────────────
        if now - last_check >= CHECK_INTERVAL:
            ts = time.strftime("%H:%M:%S")
            print(f"\n[{ts}] Плановая проверка...")

            print("[ECO]")
            scan_and_apply_eco()

            print("[LAYOUT]")
            windows = get_ldplayer_windows()
            if windows:
                arrange_windows(windows)
            else:
                print("  [LAYOUT] Окна не найдены")

            last_check = time.time()

        # ── Переключение окон ──────────────────────────────────
        windows = get_ldplayer_windows()

        if not windows:
            print("  [КЛИК] Окна не найдены, жду...", end="\r")
            time.sleep(2)
            continue

        for hwnd, pid, title in windows:
            if stop_flag or paused:
                break
            bring_window_and_click(hwnd, title)
            for _ in range(WINDOW_SWITCH_DELAY * 2):
                if stop_flag or paused:
                    break
                time.sleep(0.5)

    print("\n[ВЫХОД] Скрипт остановлен.")


if __name__ == "__main__":
    main()
