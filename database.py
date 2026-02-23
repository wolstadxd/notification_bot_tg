import json
import os

CHATS_FILE = "chats.json"
ALLOWED_USERS_FILE = "allowed_users.json"
TEMPLATES_FILE = "templates.json"

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
        # Якщо файл не існує, повертаємо порожній список
        return []

def save_allowed_users(users_list):
    with open(ALLOWED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_list, f, ensure_ascii=False, indent=4)

# Функції для роботи з шаблонами
def load_templates():
    try:
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Якщо файл не існує, повертаємо порожній словник
        return {}

def save_templates(templates_dict):
    with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(templates_dict, f, ensure_ascii=False, indent=4)