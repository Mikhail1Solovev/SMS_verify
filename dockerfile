# Dockerfile

# Используем официальный образ Python в качестве базового
FROM python:3.10-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем директорию для приложения
WORKDIR /code

# Копируем и устанавливаем зависимости
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем код приложения
COPY . /code/

# Собираем статику
RUN python manage.py collectstatic --noinput

# Запускаем приложение
CMD ["gunicorn", "referral_project.wsgi:application", "--bind", "0.0.0.0:8000"]
