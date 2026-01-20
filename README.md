# Telegram Broadcast Bot

Бот для розсилки повідомлень у Telegram чати з підтримкою гео-тегів та мов.

## Встановлення

1. Клонуй репозиторій:
```bash
git clone <your-repo-url>
cd lfbot
```

2. Створи віртуальне середовище:
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# або
.venv\Scripts\activate  # Windows
```

3. Встанови залежності:
```bash
pip install -r requirements.txt
```

4. Створи файл `.env` в корені проєкту:
```env
BOT_TOKEN=твій_токен_від_BotFather
```

5. Запусти бота:
```bash
python main.py
```

## Використання

- `/admin` - відкрити адмін-панель (тільки для дозволених користувачів)
- `/start` - отримати свій Chat ID

## Структура проєкту

```
lfbot/
├── handlers/       # Обробники команд та callback'ів
├── keyboards.py    # Інлайн-клавіатури
├── config.py       # Конфігурація (чати, шаблони, користувачі)
├── main.py         # Точка входу
└── requirements.txt
```
