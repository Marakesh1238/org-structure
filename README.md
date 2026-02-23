# Organization Structure API

REST API для управления иерархической структурой организации (подразделения и сотрудники). Проект реализован на FastAPI с использованием асинхронной SQLAlchemy, поддерживает миграции Alembic, полностью докеризирован и покрыт тестами.

## Технологический стек

- **FastAPI** – современный веб-фреймворк для создания API
- **SQLAlchemy 2.0** (async) – ORM для работы с PostgreSQL
- **Alembic** – управление миграциями базы данных
- **Pydantic v2** – валидация данных и OpenAPI-схемы
- **PostgreSQL** – реляционная база данных
- **Docker / Docker Compose** – контейнеризация и оркестрация
- **pytest / pytest-asyncio / httpx** – тестирование эндпоинтов
- **Poetry** – управление зависимостями Python

## Требования

- Python 3.12+
- Docker и Docker Compose (для запуска в контейнерах)
- PostgreSQL (локально или в Docker)
- Poetry (опционально, для локальной разработки)

## Быстрый старт

### 1. Клонирование репозитория

git clone https://github.com/Marakesh1238/org-structure.git
cd org-structure

### 2.Запуск проекта

docker-compose up --build

После успешного запуска будут доступны:

API: http://localhost:8000

Документация OpenAPI: http://localhost:8000/docs

pgAdmin (веб-интерфейс для БД): http://localhost:8080
Логин: admin@example.com
Движок : PostgreSQL
Cервер: db
Имя пользователя: postgres
Пароль: postgres
База данных	: org_structure

### Миграции:

poetry run alembic upgrade head

### Фикстуры для проекта

poetry run python -m app.seed

### Тесты

poetry run pytest -v

