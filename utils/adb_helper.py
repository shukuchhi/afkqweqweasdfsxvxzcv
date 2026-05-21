"""
ADB Helper — координация между инстансами при рестарте ADB-сервера.

ПРОБЛЕМА: эмулятор теряет ADB. kill-server помогает, но роняет остальных.
РЕШЕНИЕ: файл-маркер restarting — пока один рестартит, остальные ЖДУТ.

ИСПОЛЬЗОВАНИЕ:
    from utils.adb_helper import adb
    adb('emulator-5562', 'shell', 'am', 'force-stop', 'com.mobile.legends')
"""

import subprocess, time, os, sys
from pathlib import Path
from typing import List

_MARKER_DIR = Path(os.environ.get('TEMP', '/tmp')) / '.adb_helper'
_MARKER_DIR.mkdir(parents=True, exist_ok=True)

_RESTARTING = _MARKER_DIR / 'restarting'
_RESTART_TS  = _MARKER_DIR / 'restart_ts'

RESTART_TIMEOUT  = 30
RESTART_COOLDOWN = 10
POLL             = 0.8


def _run(cmd: list, timeout: int = 15) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, -1, stdout='', stderr='Timeout')
    except Exception as e:
        return subprocess.CompletedProcess(cmd, -1, stdout='', stderr=str(e))


def _is_lost(r: subprocess.CompletedProcess) -> bool:
    t = (r.stderr + r.stdout).lower()
    return any(x in t for x in ('device', 'not found', 'offline', 'no device')) and (
        'error' in t or 'not found' in t or 'offline' in t or 'no device' in t
    )


# ── МАРКЕР ────────────────────────────────────

def _now_restarting() -> bool:
    if not _RESTARTING.exists():
        return False
    try:
        if time.time() - _RESTARTING.stat().st_mtime > RESTART_TIMEOUT:
            _RESTARTING.unlink(missing_ok=True)
            return False
        return True
    except OSError:
        return False


def _set():   _RESTARTING.touch()
def _clear(): _RESTARTING.unlink(missing_ok=True); _RESTART_TS.write_text(str(time.time()))


def _wait():
    if not _now_restarting():
        return
    print("[ADB] ⏳ другой инстанс рестартит сервер, жду...")
    t0 = time.time()
    while _now_restarting() and (time.time() - t0) < RESTART_TIMEOUT:
        time.sleep(POLL)
    print(f"[ADB] ✅ дождался ({time.time()-t0:.0f}с)")


# ── РЕСТАРТ ───────────────────────────────────

def restart_adb_server() -> bool:
    """kill-server + start-server. Ставит маркер — остальные ждут."""
    if _RESTART_TS.exists():
        try:
            if time.time() - float(_RESTART_TS.read_text().strip()) < RESTART_COOLDOWN:
                print("[ADB] ⏭️ сервер уже рестартили недавно")
                return True
        except (ValueError, OSError):
            pass

    _set()
    try:
        print("[ADB] 🔴 kill-server...")
        subprocess.run(['adb', 'kill-server'], capture_output=True, timeout=5)
        time.sleep(1)
        print("[ADB] 🟢 start-server...")
        subprocess.run(['adb', 'start-server'], capture_output=True, timeout=10)
        time.sleep(2)
        print("[ADB] ⏳ жду авто-обнаружения (5с)...")
        time.sleep(5)
        devs = get_devices()
        print(f"[ADB] ✅ сервер жив, устройств: {len(devs)}")
        for d in devs:
            print(f"       {d}")
        return True
    finally:
        _clear()


# ── УСТРОЙСТВА ────────────────────────────────

def get_devices() -> List[str]:
    _run(['adb', 'start-server'], timeout=5)
    r = _run(['adb', 'devices'], timeout=5)
    devs = []
    for line in r.stdout.strip().split('\n')[1:]:
        p = line.split()
        if len(p) >= 2 and p[1] == 'device':
            devs.append(p[0])
    return devs


def is_online(serial: str) -> bool:
    return serial in get_devices()


def check_adb_devices() -> bool:
    """Есть ли хоть одно устройство? (замена размазанной по модулям функции)"""
    devs = get_devices()
    print(f"[ADB] устройств: {len(devs)}")
    for d in devs:
        print(f"       {d}")
    return len(devs) > 0


# ── ГЛАВНОЕ: БЕЗОПАСНЫЙ ADB-ВЫЗОВ ─────────────

def adb(serial: str, *args: str, timeout: int = 20, retries: int = 4) -> None:
    """
    Выполнить ADB-команду с защитой от kill-server.
    Если девайс потерян — ждёт или рестартит сервер, ретраит.
    """
    cmd = ['adb', '-s', serial] + list(args)

    for attempt in range(1, retries + 1):
        _wait()

        r = _run(cmd, timeout=timeout)
        if r.returncode == 0:
            return

        if _is_lost(r):
            print(f"[ADB] 🔻 {serial} потерян ({attempt}/{retries})")
            if _now_restarting():
                print("[ADB]   жду чужой рестарт...")
                _wait()
            else:
                restart_adb_server()
            time.sleep(2)
            continue

        err = r.stderr.strip()[:200]
        print(f"[ADB] ⚠️ ошибка ({attempt}/{retries}): {err}")
        if attempt < retries:
            time.sleep(1.5)

    raise RuntimeError(f"ADB: исчерпаны попытки ({retries}) на {serial}")


def run_adb(cmd_list: list, timeout: int = 20, retries: int = 4) -> subprocess.CompletedProcess:
    """
    Обёртка для замены subprocess.run(['adb', '-s', serial, ...]).
    """
    serial = None
    for i, a in enumerate(cmd_list):
        if a == '-s' and i + 1 < len(cmd_list):
            serial = cmd_list[i + 1]
            break
    if serial is None:
        return subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)

    idx = cmd_list.index('-s')
    args_after = cmd_list[idx + 2:]
    try:
        adb(serial, *args_after, timeout=timeout, retries=retries)
        return subprocess.CompletedProcess(cmd_list, 0, stdout='', stderr='')
    except RuntimeError as e:
        return subprocess.CompletedProcess(cmd_list, 1, stdout='', stderr=str(e))


# ── ТЕСТ ──────────────────────────────────────

if __name__ == '__main__':
    print('=== ADB Helper ===')
    print(f'Маркеры: {_MARKER_DIR}')
    devs = get_devices()
    print(f'Устройств: {len(devs)}')
    for d in devs:
        print(f'  {d}')
    if devs:
        print(f'\nТест на {devs[0]}...')
        adb(devs[0], 'shell', 'echo', 'OK')
        print('  ✅')
    print('=== Готово ===')