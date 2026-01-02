# Архитектура системы управления Telegram user-аккаунтами

## Обзор системы

Система предназначена для управления несколькими Telegram user-аккаунтами через MTProto API, которые ведут себя как живые люди с развивающейся личностью, памятью и недетерминированным поведением.

## Принципы проектирования

1. **Автономность**: Каждый аккаунт работает независимо
2. **Недетерминированность**: Поведение не предсказуемо на 100%
3. **Саморазвитие**: Личность эволюционирует на основе опыта
4. **Контекстность**: Все решения принимаются с учетом истории
5. **Безопасность**: Никакого спама, фрода или накруток

---

## Архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                    Control API Layer                         │
│  (REST API для управления аккаунтами извне)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Account Manager (Orchestrator)                   │
│  - Управление жизненным циклом аккаунтов                      │
│  - Распределение ресурсов                                     │
│  - Мониторинг состояния                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐
│  Account 1   │ │ Account 2 │ │ Account N │
│  (Persona)   │ │ (Persona) │ │ (Persona)  │
└───────┬──────┘ └─────┬─────┘ └─────┬─────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼────┐  ┌──────────▼──────────┐  ┌───▼────┐
│Listener│  │  Decision Engine    │  │ Memory │
│(MTProto)│  │  (Response Logic)   │  │ System │
└───┬────┘  └──────────┬──────────┘  └───┬────┘
    │                  │                  │
    └──────────────────┼──────────────────┘
                       │
              ┌────────▼────────┐
              │   LLM Service   │
              │  (Response Gen) │
              └─────────────────┘
                       │
              ┌────────▼────────┐
              │  Database Layer │
              │  (SQLite/PostgreSQL)│
              └─────────────────┘
```

---

## Модули системы

### 1. Account Manager (Orchestrator)

**Ответственность:**
- Инициализация и управление аккаунтами
- Загрузка конфигураций
- Мониторинг состояния
- Управление ресурсами

**Ключевые компоненты:**
- `AccountRegistry`: Реестр всех активных аккаунтов
- `ConfigLoader`: Загрузка конфигураций из файлов/БД
- `HealthMonitor`: Мониторинг состояния аккаунтов

---

### 2. Listener Module (MTProto)

**Ответственность:**
- Подключение к Telegram через MTProto
- Подписка на события новых сообщений
- Парсинг входящих сообщений
- Извлечение контекста (thread, reply, mentions)

**Ключевые компоненты:**
- `MTProtoClient`: Обертка над Telethon/Pyrogram
- `MessageParser`: Парсинг сообщений и извлечение метаданных
- `EventDispatcher`: Распределение событий в систему

**События:**
- `NewMessage`: Новое сообщение в чате/канале
- `MessageEdit`: Редактирование сообщения
- `Reaction`: Реакция на сообщение
- `UserUpdate`: Изменение профиля пользователя

---

### 3. Decision Engine

**Ответственность:**
- Анализ входящих сообщений
- Принятие решения: отвечать / игнорировать / отложить
- Расчет вероятности ответа
- Управление cooldown и активными часами

**Pipeline принятия решения:**

```
Входящее сообщение
    │
    ├─→ Парсинг контекста
    │   ├─ Адресовано ли мне?
    │   ├─ Тема обсуждения
    │   ├─ Тон диалога
    │   └─ Активность в чате
    │
    ├─→ Проверка правил
    │   ├─ Активные часы?
    │   ├─ Cooldown прошёл?
    │   ├─ Запрещённые темы?
    │   └─ Уровень автономности
    │
    ├─→ Оценка важности
    │   ├─ Прямое обращение: +0.3
    │   ├─ Интересная тема: +0.2
    │   ├─ Вопрос: +0.15
    │   ├─ Флейм: -0.3
    │   └─ Недавно писал: -0.2
    │
    ├─→ Расчет вероятности
    │   P(response) = base_probability + importance_score
    │
    └─→ Принятие решения
        ├─ Ответить (P > threshold)
        ├─ Отреагировать (P средний)
        ├─ Игнорировать (P низкий)
        └─ Отложить (не активные часы)
```

**Ключевые компоненты:**
- `ContextAnalyzer`: Анализ контекста сообщения
- `ImportanceScorer`: Расчет важности сообщения
- `DecisionMaker`: Финальное принятие решения
- `CooldownManager`: Управление задержками

---

### 4. Memory System

**Ответственность:**
- Хранение истории диалогов
- Кэширование контекста чатов
- Запоминание позиций и мнений
- Трекинг взаимодействий с пользователями

**Структура памяти:**

```
Memory
├─ Chat History (последние N сообщений)
├─ User Profiles (стиль общения конкретных людей)
├─ Topic Memory (позиции по темам)
├─ Interaction Log (история взаимодействий)
└─ Context Cache (текущий контекст чатов)
```

**Ключевые компоненты:**
- `ChatMemory`: История конкретного чата
- `UserMemory`: Профили пользователей
- `TopicMemory`: Позиции по темам
- `MemoryManager`: Управление всей памятью

---

### 5. Personality Engine

**Ответственность:**
- Управление профилем личности
- Динамическое развитие личности
- Применение стиля в ответах
- Эволюция на основе опыта

**Структура личности:**

```python
PersonalityProfile {
    # Базовые параметры (задаются вручную)
    base: {
        speech_style: str,
        message_length: str,
        emoji_usage: str,
        interests: List[str],
        active_hours: Dict,
        activity_probability: float
    },
    
    # Динамические параметры (эволюционируют)
    dynamic: {
        discussion_tendency: float,  # Склонность к дискуссиям
        activity_level: float,        # Уровень активности
        topic_priorities: Dict,       # Приоритеты тем
        user_relationships: Dict     # Отношения с пользователями
    },
    
    # Ограничения
    constraints: {
        personality_locked: bool,     # Заблокирована ли личность
        evolution_enabled: bool,       # Включено ли развитие
        autonomy_level: float         # Уровень автономности
    }
}
```

**Эволюция личности:**

- Медленные изменения (0.01-0.05 за событие)
- Ограничения на диапазоны значений
- Без резких скачков
- Логирование всех изменений

**Ключевые компоненты:**
- `PersonalityProfile`: Профиль личности
- `EvolutionEngine`: Движок эволюции
- `StyleApplicator`: Применение стиля к ответам

---

### 6. LLM Service

**Ответственность:**
- Генерация контекстных ответов
- Адаптация под стиль личности
- Учет истории диалога
- Разнообразие ответов

**Prompt структура:**

```
System: Ты — [persona_name], [speech_style] человек.
Интересы: [interests]
Стиль общения: [message_length], [emoji_usage]

Контекст диалога:
[последние N сообщений]

Память:
[релевантная память о пользователях/темах]

Задача: Ответь на сообщение [message] в стиле своей личности.
Учти:
- Не повторяй предыдущие мысли
- Будь естественным
- Используй стиль [speech_style]
- Длина: [message_length]
```

**Ключевые компоненты:**
- `PromptBuilder`: Построение промптов
- `LLMClient`: Интеграция с LLM (OpenAI/Anthropic/Local)
- `ResponseFormatter`: Форматирование ответов

---

### 7. Control API

**Ответственность:**
- REST API для управления извне
- Изменение параметров личности
- Мониторинг состояния
- Управление аккаунтами

**Endpoints:**
- `GET /accounts` - Список аккаунтов
- `GET /accounts/{id}/profile` - Профиль личности
- `PUT /accounts/{id}/profile` - Обновление профиля
- `POST /accounts/{id}/lock` - Блокировка личности
- `GET /accounts/{id}/memory` - Просмотр памяти
- `POST /accounts/{id}/memory/clear` - Очистка памяти
- `GET /accounts/{id}/stats` - Статистика активности

---

## Структура базы данных

### Таблица: accounts
```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT UNIQUE NOT NULL,
    session_file TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP
);
```

### Таблица: personality_profiles
```sql
CREATE TABLE personality_profiles (
    account_id INTEGER PRIMARY KEY,
    base_config JSON NOT NULL,
    dynamic_config JSON NOT NULL,
    constraints_config JSON NOT NULL,
    evolution_enabled BOOLEAN DEFAULT TRUE,
    personality_locked BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);
```

### Таблица: chat_memory
```sql
CREATE TABLE chat_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    chat_id TEXT NOT NULL,
    message_id INTEGER,
    user_id TEXT,
    username TEXT,
    message_text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_reply_to INTEGER,
    context_data JSON,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);
CREATE INDEX idx_chat_memory_account_chat ON chat_memory(account_id, chat_id, timestamp);
```

### Таблица: user_profiles
```sql
CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    username TEXT,
    interaction_count INTEGER DEFAULT 0,
    last_interaction TIMESTAMP,
    communication_style JSON,
    relationship_score REAL DEFAULT 0.5,
    notes TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    UNIQUE(account_id, user_id)
);
```

### Таблица: topic_memory
```sql
CREATE TABLE topic_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    topic_keyword TEXT NOT NULL,
    position TEXT,
    priority REAL DEFAULT 0.5,
    last_discussed TIMESTAMP,
    discussion_count INTEGER DEFAULT 0,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    UNIQUE(account_id, topic_keyword)
);
```

### Таблица: interaction_log
```sql
CREATE TABLE interaction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    chat_id TEXT NOT NULL,
    action_type TEXT NOT NULL, -- 'message', 'reaction', 'ignore'
    message_id INTEGER,
    response_text TEXT,
    importance_score REAL,
    decision_reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);
CREATE INDEX idx_interaction_log_account_time ON interaction_log(account_id, timestamp);
```

### Таблица: evolution_history
```sql
CREATE TABLE evolution_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    parameter_name TEXT NOT NULL,
    old_value REAL,
    new_value REAL,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);
```

---

## Потоки данных

### Поток обработки входящего сообщения

```
1. Listener получает новое сообщение через MTProto
   │
2. MessageParser извлекает контекст
   │
3. Decision Engine анализирует:
   ├─ ContextAnalyzer: парсит контекст
   ├─ CooldownManager: проверяет задержки
   ├─ ImportanceScorer: рассчитывает важность
   └─ DecisionMaker: принимает решение
   │
4. Если решение = "ответить":
   │
5. Memory System предоставляет контекст:
   ├─ ChatMemory: последние сообщения
   ├─ UserMemory: профиль отправителя
   └─ TopicMemory: позиции по теме
   │
6. Personality Engine формирует стиль
   │
7. LLM Service генерирует ответ:
   ├─ PromptBuilder: строит промпт
   ├─ LLMClient: генерирует текст
   └─ ResponseFormatter: форматирует
   │
8. Применяется задержка (30 сек - 2 часа)
   │
9. Отправка сообщения через MTProto
   │
10. Memory System обновляет память
    │
11. Personality Engine обновляет динамические параметры
    │
12. Interaction Log записывает событие
```

---

## Безопасность и этика

1. **Rate Limiting**: Ограничение частоты сообщений
2. **Cooldown**: Минимальные задержки между ответами
3. **Content Filter**: Фильтрация запрещенных тем
4. **Monitoring**: Мониторинг активности на аномалии
5. **Manual Override**: Возможность остановить аккаунт вручную

---

## Масштабируемость

- Каждый аккаунт работает в отдельном процессе/потоке
- Общая БД для всех аккаунтов
- Возможность горизонтального масштабирования
- Кэширование для производительности

---

## Технологический стек

- **MTProto**: Telethon или Pyrogram
- **LLM**: OpenAI API / Anthropic Claude / Local LLM (Ollama)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **API**: FastAPI для Control API
- **Language**: Python 3.10+

---

## Следующие шаги

1. Реализация базовых модулей
2. Интеграция MTProto
3. Настройка LLM
4. Тестирование на одном аккаунте
5. Масштабирование на несколько аккаунтов

