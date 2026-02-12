import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN env var is not set")

HISTORY_FILE = "sent_history.json"
LOG_FILE = "activity_log.json"

def write_event_log(event_type, details):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "details": details
    }

    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            try:
                logs = json.load(f)
            except: logs = []

    logs.append(log_entry)

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

def save_history(history_data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=4)

def load_history():
    """Завантажує історію при старті бота"""
    if not os.path.exists(HISTORY_FILE):
        save_history({})
        return {}
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            raw = f.read().strip()
            return json.loads(raw) if raw else {}
    except Exception as e:
        print(f"Помилка при читанні JSON: {e}")
        return {}

# Тепер при запуску бота історія завжди підтягнеться коректно
sent_history = load_history()

CHATS = [
    {"name": "Чат Перу", "id": -5085462955, "tags": ["peru", "en"], "mentions": ["@test1", "@test2"]},
    {"name": "Чат Перу", "id": -5229326817, "tags": ["peru", "ru"], "mentions": ["@test3", "@test4"]},
    {"name": "Чат Україна", "id": -5093445860, "tags": ["ua", "ua"], "mentions": ["@test5", "@test6"]},
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