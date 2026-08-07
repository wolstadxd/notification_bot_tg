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