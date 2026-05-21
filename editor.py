# settings_editor.py
import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_settings.json")

# ============================================================
#   ЗДЕСЬ ДОБАВЛЯЙ СВОИ ВОПРОСЫ И ОТВЕТЫ
#   Формат:
#   {
#       "ключ_в_json": {
#           "question": "Твой вопрос?",
#           "options": {
#               "1": {"label": "Описание варианта 1", "value": значение},
#               "2": {"label": "Описание варианта 2", "value": значение},
#           }
#       }
#   }
# ============================================================

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


def load_settings():
    """Загружает текущие настройки из JSON."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_settings(settings: dict):
    """Сохраняет настройки в JSON."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)
    print(f"\n✅ Настройки сохранены в '{SETTINGS_FILE}'")


def ask_questions():
    """Задаёт все вопросы пользователю и возвращает словарь с ответами."""
    print("\n" + "="*50)
    print("       НАСТРОЙКА БОТА")
    print("="*50)

    settings = load_settings()

    for key, data in QUESTIONS.items():
        print(f"\n❓ {data['question']}")

        # Показываем варианты ответов
        for num, option in data["options"].items():
            print(f"   {num} - {option['label']}")

        # Показываем текущее значение если есть
        if key in settings:
            current = settings[key]
            print(f"   (Текущее значение: {current} | Enter = оставить)")

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

    return settings


def main():
    settings = ask_questions()
    save_settings(settings)

    # Показываем итог
    print("\n📋 Итоговые настройки:")
    print(json.dumps(settings, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()