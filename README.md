# Реферальная Система на Django

## Описание Проекта

В рамках данного проекта реализована реферальная система, позволяющая пользователям регистрироваться и авторизовываться по номеру телефона, а также использовать и распространять инвайт-коды. Система включает API для взаимодействия и простой интерфейс на Django Templates для базового тестирования.

## Структура Проекта

- **accounts/**: Приложение Django для управления пользователями и реферальными кодами.
- **referral_project/**: Конфигурация проекта Django.
- **templates/**: HTML шаблоны для интерфейса.
- **docker-compose.yml**: Файл для контейнеризации с помощью Docker Compose.
- **Dockerfile**: Файл для сборки Docker образа.
- **requirements.txt**: Список зависимостей проекта.
- **README.md**: Документация проекта.

## Установка и Запуск

### Предварительные Требования

- Docker
- Docker Compose

### Шаги по Развертыванию

1. **Клонирование Репозитория**

   ```bash
   git clone https:https://github.com/Mikhail1Solovev/SMS_verify.git
   cd referral_project
   ```

2. **Создайте файл .env в корне проекта**

3. **Сборка и Запуск Контейнеров**
```bash
  docker-compose up --build


