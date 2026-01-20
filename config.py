import json
import os
from dotenv import load_dotenv

load_dotenv()  # підтягуємо змінні з .env, якщо файл є

TOKEN = os.getenv("BOT_TOKEN", "")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN env var is not set")

HISTORY_FILE = "sent_history.json"

def save_history(data):
    """Зберігає історію у файл"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_history():
    """Завантажує історію, створюючи файл за потреби"""
    # 1. Перевіряємо, чи існує файл
    if not os.path.exists(HISTORY_FILE):
        # Якщо файлу немає — створюємо його з пустим словником всередині
        save_history({})
        return {}

    # 2. Якщо файл є, читаємо його з перевіркою на порожнечу (Варіант №1)
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            raw = f.read().strip()
            if not raw:
                return {}
            return json.loads(raw)
    except Exception as e:
        print(f"Помилка при читанні JSON: {e}")
        return {}

# Тепер при запуску бота історія завжди підтягнеться коректно
sent_history = load_history()

CHATS = [
    {"name": "Чат Перу", 
     "id": -5085462955, 
     "tags": ["peru", "en"], 
     "mentions": ["@test1", "@test2"]},
    {"name": "Чат Перу", 
    "id": -5229326817, 
    "tags": ["peru", "ru", "en"],
     "mentions": ["@test3", "@test4"]},
    {"name": "Чат Україна", 
    "id": -5093445860, 
    "tags": ["ua", "ua"],
     "mentions": ["@test5", "@test6"]},
]

ALLOWED_USERS = [437279092, 6812779400]

TEMPLATES = {
    "ua": {
        "low_sr": "📉 **Low Success Rate**\nСпостерігається зниження конверсії по напрямку {geo}. Технічний відділ вже займається.",
        "tech": "⚙️ **Техроботи**\nНа стороні банку-партнера в {geo} проводяться планові роботи. ETA: 2 години.",
        "fixed": "✅ **Відновлено**\nРобота по напрямку {geo} стабілізована. Все працює в штатному режимі."
    },
    "ru": {
        "low_sr": "📉 **Low Success Rate**\nНаблюдается снижение конверсии по направлению {geo}. Технический отдел уже занимается.",
        "tech": "⚙️ **Техработы**\nНа стороне банка-партнера в {geo} проводятся плановые работы. ETA: 2 часа.",
        "fixed": "✅ **Восстановлено**\nРабота по направлению {geo} стабилизирована. Все работает в штатном режиме."
    },
    "en": {
        "low_sr": "📉 **Low Success Rate**\nConversion drop detected for {geo}. Technical department is already investigating.",
        "tech": "⚙️ **Maintenance**\nScheduled maintenance on the partner bank's side in {geo}. ETA: 2 hours.",
        "fixed": "✅ **Restored**\nOperations for {geo} have been stabilized. Everything is working normally."
    },
}