# Система управления Telegram user-аккаунтами

Полнофункциональная система для управления несколькими Telegram user-аккаунтами через MTProto, которые ведут себя как живые люди с развивающейся личностью.

## Возможности

- ✅ Чтение сообщений через MTProto (Telethon)
- ✅ Анализ контекста и принятие решений
- ✅ Генерация логичных ответов через LLM
- ✅ Система памяти (история, пользователи, темы)
- ✅ Развивающаяся личность на основе опыта
- ✅ REST API для управления извне
- ✅ Недетерминированное поведение
- ✅ Защита от спама и накруток

## Установка

### 1. Установить зависимости

```bash
pip install -r requirements.txt
```

### 2. Получить Telegram API credentials

1. Перейдите на https://my.telegram.org/apps
2. Создайте приложение
3. Получите `api_id` и `api_hash`

### 3. Создать сессию для аккаунта

```bash
python examples/create_session.py
```

Сохраните полученную строку сессии.

### 4. Настроить переменные окружения

Создайте `.env` файл:

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_SESSION_STRING=your_session_string_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Быстрый старт

```python
import asyncio
from user_accounts_system.orchestrator import Orchestrator
import os

async def main():
    orchestrator = Orchestrator(
        db_path="data/accounts.db",
        llm_provider="openai",
        llm_api_key=os.getenv("OPENAI_API_KEY"),
        llm_model="gpt-4o-mini",
    )
    
    # Зарегистрировать аккаунт
    account_id = orchestrator.register_account(
        phone_number="+1234567890",
        session_string=os.getenv("TELEGRAM_SESSION_STRING"),
        api_id=int(os.getenv("TELEGRAM_API_ID")),
        api_hash=os.getenv("TELEGRAM_API_HASH"),
    )
    
    # Запустить
    await orchestrator.start_account(account_id)
    
    # Работать...
    await asyncio.sleep(3600)
    
    # Остановить
    await orchestrator.stop_all()

asyncio.run(main())
```

## Структура проекта

```
user_accounts_system/
├── database/          # Модели БД и менеджер
├── listener/          # MTProto listener для сообщений
├── decision/          # Движок принятия решений
├── memory/            # Система памяти
├── personality/       # Управление личностью
├── llm/               # Интеграция с LLM
├── api/               # REST API
├── account_manager.py # Менеджер одного аккаунта
└── orchestrator.py    # Главный orchestrator
```

## Настройка личности

### Через код

```python
from user_accounts_system.database.models import (
    BasePersonalityConfig,
    DynamicPersonalityConfig,
    PersonalityConstraints,
    PersonalityProfile,
)

profile = PersonalityProfile(
    account_id=1,
    base=BasePersonalityConfig(
        speech_style="ироничный",
        message_length="средний",
        emoji_usage="редко",
        interests=["IT", "крипта"],
        active_hours={
            "preferred": ["evening", "night"],
            "timezone": "UTC+3"
        },
        activity_probability=0.35,
    ),
    dynamic=DynamicPersonalityConfig(
        discussion_tendency=0.5,
        activity_level=0.5,
    ),
    constraints=PersonalityConstraints(
        personality_locked=False,
        evolution_enabled=True,
        autonomy_level=0.8,
    ),
)
```

### Через API

```bash
curl -X PUT http://localhost:8000/accounts/1/profile \
  -H "Content-Type: application/json" \
  -d '{
    "base_config": {
      "speech_style": "формальный",
      "activity_probability": 0.5
    }
  }'
```

## REST API

Запуск API сервера:

```python
from user_accounts_system.orchestrator import Orchestrator
from user_accounts_system.api.control_api import create_app
import uvicorn

orchestrator = Orchestrator(...)
app = create_app(orchestrator)
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Endpoints

- `GET /accounts` - Список аккаунтов
- `GET /accounts/{id}` - Информация об аккаунте
- `GET /accounts/{id}/profile` - Профиль личности
- `PUT /accounts/{id}/profile` - Обновить профиль
- `POST /accounts/{id}/profile/lock` - Заблокировать личность
- `GET /accounts/{id}/memory` - Память аккаунта
- `GET /accounts/{id}/stats` - Статистика

Подробнее: `examples/api_usage_examples.md`

## Архитектура

Подробное описание архитектуры: `docs/ARCHITECTURE.md`

### Основные компоненты

1. **Listener** - Прослушивание сообщений через MTProto
2. **Decision Engine** - Принятие решений о ответах
3. **Memory System** - Хранение контекста и истории
4. **Personality Engine** - Управление и развитие личности
5. **LLM Service** - Генерация ответов

### Поток обработки

```
Сообщение → Парсинг → Анализ → Решение → Генерация → Отправка → Эволюция
```

## Безопасность

- ✅ Rate limiting (cooldown между ответами)
- ✅ Проверка активных часов
- ✅ Фильтрация запрещенных тем/пользователей
- ✅ Ограничение автономности
- ✅ Мониторинг активности

## Эволюция личности

Личность эволюционирует на основе опыта:

- **Ответил** → ↑ активность
- **Дискуссия** → ↑ склонность к обсуждениям
- **Положительная реакция** → ↑ активность
- **Игнорировал** → ↓ активность

Изменения медленные (2-5% за событие) для реалистичности.

## Примеры

- `examples/basic_usage.py` - Базовое использование
- `examples/create_session.py` - Создание сессии
- `examples/config_example.json` - Пример конфигурации

## Документация

- `docs/ARCHITECTURE.md` - Архитектура системы
- `docs/DECISION_TREE.md` - Дерево принятия решений
- `docs/PROMPT_EXAMPLES.md` - Примеры промптов

## Важные замечания

⚠️ **Этика использования:**
- Не используйте для спама
- Не используйте для накруток
- Соблюдайте правила Telegram
- Уважайте других пользователей

⚠️ **Технические ограничения:**
- Система требует LLM API (OpenAI/Anthropic/Local)
- Нужны валидные Telegram сессии
- База данных SQLite (можно переключить на PostgreSQL)

## Лицензия

Этот код предоставлен как есть, для образовательных целей.

