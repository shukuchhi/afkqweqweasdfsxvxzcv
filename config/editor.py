# settings_editor.py
import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_settings.json")

# ============================================================
# ВОПРОСЫ НАСТРОЙКИ
# ============================================================

QUESTIONS = {
    "tickets_count": {
        "question": "На аккаунте сколько билетов?",
        "options": {
            "1": {"label": "0 билетов",   "value": 0},
            "2": {"label": "200 билетов", "value": 200},
        }
    },

    "region": {
        "question": "Регион аккаунтов?",
        "options": {
            "1": {"label": "RU  (VPN не нужен)", "value": "ru"},
            "2": {"label": "Global (нужен VPN)", "value": "global"},
        }
    },
}

# ============================================================

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)
    print(f"\n✅ Настройки сохранены в '{SETTINGS_FILE}'")

def ask_questions():
    print("\n" + "=" * 50)
    print(" НАСТРОЙКА БОТА")
    print("=" * 50)

    settings = load_settings()

    for key, data in QUESTIONS.items():
        print(f"\n❓ {data['question']}")

        for num, option in data["options"].items():
            print(f"   {num} - {option['label']}")

        if key in settings:
            print(f"   (Текущее значение: {settings[key]} | Enter = оставить)")

        while True:
            user_input = input("   Твой выбор: ").strip()

            if user_input == "" and key in settings:
                print(f"   ↩️  Оставлено: {settings[key]}")
                break

            if user_input in data["options"]:
                settings[key] = data["options"][user_input]["value"]
                print(f"   ✔️  Выбрано: {data['options'][user_input]['label']}")
                break
            else:
                valid = ", ".join(data["options"].keys())
                print(f"   ⚠️  Неверный ввод. Введи одно из: {valid}")

    return settings

def main():
    settings = ask_questions()
    save_settings(settings)

    print("\n📋 Итоговые настройки:")
    print(json.dumps(settings, ensure_ascii=False, indent=4))

    # Подсказка если глобал
    if settings.get("region") == "global":
        print("\n💡 Регион: Global — VPN (warp-cli) будет включаться автоматически.")
    else:
        print("\n💡 Регион: RU — VPN не используется.")

if __name__ == "__main__":
    main()
