# 1. Беремо офіційний образ Python
FROM python:3.11-slim

# 2. Вказуємо робочу директорію всередині контейнера
WORKDIR /app

# 3. Копіюємо файл залежностей
COPY requirements.txt .

# 4. Встановлюємо бібліотеки
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копіюємо решту файлів (код бота, шаблони тощо)
COPY . .

# 6. Запускаємо бота
CMD ["python", "main.py"]