# Используем официальный Python 3.12 как базовый образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы проекта в контейнер
COPY . /app

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем зависимости из requirements.txt
RUN pip install -r requirements.txt

# Если используешь FastAPI (для API), то можешь указать порт
EXPOSE 8000

# Команда для запуска бота (зависит от названия твоего скрипта)
CMD ["python", "bot.py"]
