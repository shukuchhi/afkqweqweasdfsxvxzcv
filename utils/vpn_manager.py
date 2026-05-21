"""
vpn_manager.py — управление Cloudflare WARP через warp-cli.

Логика:
  - region == "global" → VPN должен быть включён
  - region == "ru"     → VPN должен быть выключен

Использование в main.py:
    from utils.vpn_manager import ensure_vpn

    ensure_vpn()   # вызывать перед каждым циклом
"""

import subprocess
import time

# Путь к warp-cli (обычно уже в PATH после установки 1.1.1.1)
WARP_CLI = "warp-cli"

# Сколько секунд ждать после connect/disconnect пока состояние применится
CONNECT_WAIT    = 5
DISCONNECT_WAIT = 3

# Сколько раз пробовать если connect завис
MAX_RETRIES = 3


def _run(args: list, timeout: int = 15) -> subprocess.CompletedProcess:
    """Запускает warp-cli и возвращает результат."""
    try:
        return subprocess.run(
            [WARP_CLI] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "warp-cli не найден. Установи Cloudflare WARP: https://1.1.1.1/"
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, -1, stdout="", stderr="Timeout")


def get_status() -> str:
    """
    Возвращает текущий статус WARP:
      "connected"    — VPN активен
      "disconnected" — VPN выключен
      "unknown"      — не удалось определить
    """
    r = _run(["status"])
    output = (r.stdout + r.stderr).lower()

    if "connected" in output and "disconnected" not in output:
        return "connected"
    elif "disconnected" in output:
        return "disconnected"
    else:
        return "unknown"


def connect(retries: int = MAX_RETRIES) -> bool:
    """
    Включает VPN. Возвращает True если успешно.
    """
    for attempt in range(1, retries + 1):
        status = get_status()
        if status == "connected":
            print("[VPN] ✅ Уже подключён")
            return True

        print(f"[VPN] 🔌 Подключаю... (попытка {attempt}/{retries})")
        _run(["connect"])
        time.sleep(CONNECT_WAIT)

        if get_status() == "connected":
            print("[VPN] ✅ Подключён успешно")
            return True
        else:
            print(f"[VPN] ⚠️ Не подключился, жду ещё...")
            time.sleep(3)

    print(f"[VPN] ❌ Не удалось подключиться после {retries} попыток")
    return False


def disconnect(retries: int = MAX_RETRIES) -> bool:
    """
    Выключает VPN. Возвращает True если успешно.
    """
    for attempt in range(1, retries + 1):
        status = get_status()
        if status == "disconnected":
            print("[VPN] ✅ Уже отключён")
            return True

        print(f"[VPN] 🔌 Отключаю... (попытка {attempt}/{retries})")
        _run(["disconnect"])
        time.sleep(DISCONNECT_WAIT)

        if get_status() == "disconnected":
            print("[VPN] ✅ Отключён успешно")
            return True
        else:
            print(f"[VPN] ⚠️ Не отключился, пробую ещё...")
            time.sleep(2)

    print(f"[VPN] ❌ Не удалось отключить после {retries} попыток")
    return False


def ensure_vpn(region: str) -> bool:
    """
    Главная функция — приводит VPN в нужное состояние в зависимости от региона.

    region == "global" → включает VPN если не включён
    region == "ru"     → выключает VPN если включён

    Возвращает True если состояние соответствует нужному.
    """
    region = region.lower().strip()

    if region == "global":
        status = get_status()
        print(f"[VPN] Регион: Global | Статус: {status}")
        if status != "connected":
            return connect()
        return True

    elif region == "ru":
        status = get_status()
        print(f"[VPN] Регион: RU | Статус: {status}")
        if status != "disconnected":
            return disconnect()
        return True

    else:
        print(f"[VPN] ⚠️ Неизвестный регион '{region}', VPN не трогаю")
        return True


def print_status():
    """Печатает текущий статус для диагностики."""
    r = _run(["status"])
    print(f"[VPN] warp-cli status:\n{r.stdout or r.stderr}")


if __name__ == "__main__":
    print_status()
