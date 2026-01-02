# Быстрый старт

## 1. Установка

```bash
pip install -r requirements.txt
```

## 2. Получить Telegram API

1. Перейдите на https://my.telegram.org/apps
2. Создайте приложение
3. Получите `api_id` и `api_hash`

## 3. Создать сессию

```bash
python examples/create_session.py
```

Сохраните строку сессии.

## 4. Настроить .env

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_STRING=your_session_string
OPENAI_API_KEY=your_openai_key
```

## 5. Запустить

```bash
python examples/basic_usage.py
```

## Основные команды API

```bash
# Список аккаунтов
curl http://localhost:8000/accounts

# Профиль личности
curl http://localhost:8000/accounts/1/profile

# Обновить активность
curl -X PUT http://localhost:8000/accounts/1/profile \
  -H "Content-Type: application/json" \
  -d '{"base_config": {"activity_probability": 0.5}}'

# Статистика
curl http://localhost:8000/accounts/1/stats
```

## Документация

- `docs/ARCHITECTURE.md` - Архитектура
- `docs/DECISION_TREE.md` - Логика решений
- `docs/PROMPT_EXAMPLES.md` - Промпты
- `README.md` - Полная документация

