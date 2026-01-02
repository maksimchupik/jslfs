# Примеры использования Control API

## Запуск API сервера

```python
from user_accounts_system.orchestrator import Orchestrator
from user_accounts_system.api.control_api import create_app
import uvicorn

orchestrator = Orchestrator(...)
app = create_app(orchestrator)

uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Примеры запросов

### 1. Получить список аккаунтов

```bash
curl http://localhost:8000/accounts
```

### 2. Получить профиль личности

```bash
curl http://localhost:8000/accounts/1/profile
```

### 3. Обновить профиль личности

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

### 4. Заблокировать личность

```bash
curl -X POST http://localhost:8000/accounts/1/profile/lock
```

### 5. Получить память чата

```bash
curl http://localhost:8000/accounts/1/memory?chat_id=-1001234567890
```

### 6. Получить статистику

```bash
curl http://localhost:8000/accounts/1/stats
```

### 7. Запустить аккаунт

```bash
curl -X POST http://localhost:8000/accounts/1/start
```

### 8. Остановить аккаунт

```bash
curl -X POST http://localhost:8000/accounts/1/stop
```

## Python примеры

```python
import requests

BASE_URL = "http://localhost:8000"

# Получить профиль
response = requests.get(f"{BASE_URL}/accounts/1/profile")
profile = response.json()

# Обновить активность
requests.put(
    f"{BASE_URL}/accounts/1/profile",
    json={
        "base_config": {
            "activity_probability": 0.6
        }
    }
)

# Заблокировать личность
requests.post(f"{BASE_URL}/accounts/1/profile/lock")

# Получить статистику
stats = requests.get(f"{BASE_URL}/accounts/1/stats").json()
print(f"Messages responded: {stats['messages_responded']}")
```

