import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN env var is not set")

DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(DATA_DIR, "sent_history.json")
LOG_FILE = os.path.join(DATA_DIR, "activity_log.json")

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