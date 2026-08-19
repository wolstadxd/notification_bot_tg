import json
import os

DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

CHATS_FILE = os.path.join(DATA_DIR, "chats.json")
ALLOWED_USERS_FILE = os.path.join(DATA_DIR, "allowed_users.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")
MAIN_TEMPLATES_FILE = os.path.join(DATA_DIR, "main_templates.json")

# Функції для роботи з чатами
def load_chats():
    try:
        with open(CHATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_chats(chats_list):
    with open(CHATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(chats_list, f, ensure_ascii=False, indent=4)

# Функції для роботи з дозволеними користувачами
def load_allowed_users():
    try:
        with open(ALLOWED_USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_allowed_users(users_list):
    with open(ALLOWED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_list, f, ensure_ascii=False, indent=4)

# Функції для роботи з шаблонами
def load_templates():
    try:
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            templates = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    # Одноразова авто-міграція: str → {text, main_template: null}
    migrated = False
    for lang, lang_templates in templates.items():
        for tmpl_name, tmpl_value in lang_templates.items():
            if isinstance(tmpl_value, str):
                lang_templates[tmpl_name] = {"text": tmpl_value, "main_template": None}
                migrated = True

    if migrated:
        save_templates(templates)

    return templates

def save_templates(templates_dict):
    with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(templates_dict, f, ensure_ascii=False, indent=4)

# Функції для роботи з головними шаблонами
def load_main_templates():
    try:
        with open(MAIN_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_main_templates(main_templates_dict):
    with open(MAIN_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(main_templates_dict, f, ensure_ascii=False, indent=4)

# Функції для роботи з історією статусів методів
METHOD_HISTORY_FILE = os.path.join(DATA_DIR, "method_status_history.json")

def load_method_history():
    try:
        with open(METHOD_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_method_history(data):
    with open(METHOD_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def record_method_broadcast(broadcast_id, geo, method, cast_type, template_name, text, success_count, error_count):
    """Записує інформацію про розсилку для методу. Зберігає стек для відкату."""
    from datetime import datetime
    data = load_method_history()
    key = f"{geo.lower()}:{method.lower()}"

    if key not in data:
        data[key] = []

    data[key].append({
        "broadcast_id": broadcast_id,
        "geo": geo.upper(),
        "method": method.lower(),
        "cast_type": cast_type,
        "template_name": template_name,
        "text": text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success_count": success_count,
        "error_count": error_count
    })

    save_method_history(data)

def remove_method_broadcast(broadcast_id):
    """Видаляє запис розсилки зі стеку. Попередня стає актуальною."""
    data = load_method_history()
    for key in list(data.keys()):
        data[key] = [r for r in data[key] if r.get("broadcast_id") != broadcast_id]
        if not data[key]:
            del data[key]
    save_method_history(data)

def get_latest_method_statuses():
    """Повертає останній статус для кожного методу, згруповано по ГЕО."""
    data = load_method_history()
    result = {}  # {geo: {method: record}}
    for key, records in data.items():
        if not records:
            continue
        latest = records[-1]
        geo = latest["geo"]
        method = latest["method"]
        if geo not in result:
            result[geo] = {}
        result[geo][method] = latest
    return result