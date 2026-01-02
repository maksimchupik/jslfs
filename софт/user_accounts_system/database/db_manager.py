"""
Менеджер базы данных для системы управления аккаунтами
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from .models import (
    Account,
    PersonalityProfile,
    ChatMessage,
    UserProfile,
    TopicMemory,
    InteractionLog,
)


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, db_path: str = "data/accounts.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Инициализация структуры БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Проверить, существует ли старая таблица с уникальным ограничением
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts';")
        table_exists = cursor.fetchone()

        if table_exists:
            # Проверить, есть ли уникальное ограничение
            cursor.execute("PRAGMA table_info(accounts)")
            columns_info = cursor.fetchall()

            # Проверить, есть ли уникальное ограничение на phone_number
            # Получить SQL определение таблицы
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='accounts';")
            table_sql = cursor.fetchone()

            if table_sql and 'UNIQUE' in table_sql[0]:
                # Создать новую таблицу без уникального ограничения
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS accounts_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        phone_number TEXT NOT NULL,
                        session_file TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP,
                        api_id INTEGER,
                        api_hash TEXT,
                        session_string TEXT
                    )
                """)

                # Скопировать данные из старой таблицы в новую
                cursor.execute("""
                    INSERT INTO accounts_new (id, phone_number, session_file, is_active, created_at, last_seen)
                    SELECT id, phone_number, session_file, is_active, created_at, last_seen FROM accounts
                """)

                # Удалить старую таблицу
                cursor.execute("DROP TABLE accounts")

                # Переименовать новую таблицу
                cursor.execute("ALTER TABLE accounts_new RENAME TO accounts")
            else:
                # Проверить, существуют ли новые колонки, и добавить их, если нет
                cursor.execute("PRAGMA table_info(accounts)")
                columns = [column[1] for column in cursor.fetchall()]

                if 'api_id' not in columns:
                    cursor.execute("ALTER TABLE accounts ADD COLUMN api_id INTEGER")
                if 'api_hash' not in columns:
                    cursor.execute("ALTER TABLE accounts ADD COLUMN api_hash TEXT")
                if 'session_string' not in columns:
                    cursor.execute("ALTER TABLE accounts ADD COLUMN session_string TEXT")
        else:
            # Создать новую таблицу с правильной структурой
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT NOT NULL,
                    session_file TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP,
                    api_id INTEGER,
                    api_hash TEXT,
                    session_string TEXT
                )
            """)

        # Закрыть соединение и открыть новое для остальных таблиц
        conn.commit()
        conn.close()

        # Открыть новое соединение для создания остальных таблиц
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица профилей личности
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personality_profiles (
                account_id INTEGER PRIMARY KEY,
                base_config TEXT NOT NULL,
                dynamic_config TEXT NOT NULL,
                constraints_config TEXT NOT NULL,
                evolution_enabled BOOLEAN DEFAULT TRUE,
                personality_locked BOOLEAN DEFAULT FALSE,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)

        # Таблица памяти чатов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                chat_id TEXT NOT NULL,
                message_id INTEGER,
                user_id TEXT,
                username TEXT,
                message_text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_reply_to INTEGER,
                context_data TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_memory_account_chat 
            ON chat_memory(account_id, chat_id, timestamp)
        """)

        # Таблица профилей пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT,
                interaction_count INTEGER DEFAULT 0,
                last_interaction TIMESTAMP,
                communication_style TEXT,
                relationship_score REAL DEFAULT 0.5,
                notes TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                UNIQUE(account_id, user_id)
            )
        """)

        # Таблица памяти тем
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                topic_keyword TEXT NOT NULL,
                position TEXT,
                priority REAL DEFAULT 0.5,
                last_discussed TIMESTAMP,
                discussion_count INTEGER DEFAULT 0,
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                UNIQUE(account_id, topic_keyword)
            )
        """)

        # Таблица лога взаимодействий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                chat_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                message_id INTEGER,
                response_text TEXT,
                importance_score REAL,
                decision_reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_interaction_log_account_time 
            ON interaction_log(account_id, timestamp)
        """)

        # Таблица истории эволюции
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                old_value REAL,
                new_value REAL,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)

        conn.commit()
        conn.close()

    # === Account methods ===

    def create_account(self, account: Account) -> int:
        """Создать новый аккаунт"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accounts (phone_number, session_file, is_active, created_at, last_seen, api_id, api_hash, session_string)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account.phone_number,
            account.session_file,
            account.is_active,
            account.created_at or datetime.now(),
            account.last_seen,
            account.api_id,
            account.api_hash,
            account.session_string
        ))
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return account_id

    def update_account(self, account: Account):
        """Обновить аккаунт"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE accounts
            SET phone_number = ?, session_file = ?, is_active = ?, last_seen = ?, api_id = ?, api_hash = ?, session_string = ?
            WHERE id = ?
        """, (
            account.phone_number,
            account.session_file,
            account.is_active,
            account.last_seen,
            account.api_id,
            account.api_hash,
            account.session_string,
            account.id
        ))
        conn.commit()
        conn.close()

    def get_account(self, account_id: int) -> Optional[Account]:
        """Получить аккаунт по ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Account(
            id=row["id"],
            phone_number=row["phone_number"],
            session_file=row["session_file"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
            api_id=row["api_id"] if "api_id" in row.keys() else None,
            api_hash=row["api_hash"] if "api_hash" in row.keys() else None,
            session_string=row["session_string"] if "session_string" in row.keys() else None,
        )

    def get_all_accounts(self) -> List[Account]:
        """Получить все аккаунты"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts")
        rows = cursor.fetchall()
        conn.close()

        return [
            Account(
                id=row["id"],
                phone_number=row["phone_number"],
                session_file=row["session_file"],
                is_active=bool(row["is_active"]),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
                api_id=row["api_id"] if "api_id" in row.keys() else None,
                api_hash=row["api_hash"] if "api_hash" in row.keys() else None,
                session_string=row["session_string"] if "session_string" in row.keys() else None,
            )
            for row in rows
        ]

    # === Personality Profile methods ===

    def save_personality_profile(self, profile: PersonalityProfile):
        """Сохранить профиль личности"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO personality_profiles 
            (account_id, base_config, dynamic_config, constraints_config, 
             evolution_enabled, personality_locked, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.account_id,
            json.dumps(profile.base.to_dict()),
            json.dumps(profile.dynamic.to_dict()),
            json.dumps(profile.constraints.to_dict()),
            profile.constraints.evolution_enabled,
            profile.constraints.personality_locked,
            datetime.now()
        ))
        conn.commit()
        conn.close()

    def get_personality_profile(self, account_id: int) -> Optional[PersonalityProfile]:
        """Получить профиль личности"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM personality_profiles WHERE account_id = ?", (account_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        base_config = json.loads(row["base_config"])
        dynamic_config = json.loads(row["dynamic_config"])
        constraints_config = json.loads(row["constraints_config"])

        from .models import (
            BasePersonalityConfig,
            DynamicPersonalityConfig,
            PersonalityConstraints,
        )

        profile = PersonalityProfile(
            account_id=account_id,
            base=BasePersonalityConfig(**base_config),
            dynamic=DynamicPersonalityConfig(**dynamic_config),
            constraints=PersonalityConstraints(**constraints_config),
            last_updated=datetime.fromisoformat(row["last_updated"]) if row["last_updated"] else None,
        )
        return profile

    # === Chat Memory methods ===

    def save_chat_message(self, message: ChatMessage) -> int:
        """Сохранить сообщение в память"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_memory 
            (account_id, chat_id, message_id, user_id, username, message_text, 
             timestamp, is_reply_to, context_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message.account_id,
            message.chat_id,
            message.message_id,
            message.user_id,
            message.username,
            message.message_text,
            message.timestamp or datetime.now(),
            message.is_reply_to,
            json.dumps(message.context_data),
        ))
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return message_id

    def get_chat_history(self, account_id: int, chat_id: str, limit: int = 50) -> List[ChatMessage]:
        """Получить историю чата"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM chat_memory 
            WHERE account_id = ? AND chat_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (account_id, chat_id, limit))
        rows = cursor.fetchall()
        conn.close()

        messages = []
        for row in rows:
            context_data = json.loads(row["context_data"]) if row["context_data"] else {}
            messages.append(ChatMessage(
                id=row["id"],
                account_id=row["account_id"],
                chat_id=row["chat_id"],
                message_id=row["message_id"],
                user_id=row["user_id"],
                username=row["username"],
                message_text=row["message_text"],
                timestamp=datetime.fromisoformat(row["timestamp"]) if row["timestamp"] else None,
                is_reply_to=row["is_reply_to"],
                context_data=context_data,
            ))
        return list(reversed(messages))  # Вернуть в хронологическом порядке

    # === User Profile methods ===

    def get_or_create_user_profile(self, account_id: int, user_id: str, username: str = None) -> UserProfile:
        """Получить или создать профиль пользователя"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM user_profiles 
            WHERE account_id = ? AND user_id = ?
        """, (account_id, user_id))
        row = cursor.fetchone()

        if row:
            conn.close()
            style = json.loads(row["communication_style"]) if row["communication_style"] else {}
            return UserProfile(
                id=row["id"],
                account_id=row["account_id"],
                user_id=row["user_id"],
                username=row["username"],
                interaction_count=row["interaction_count"],
                last_interaction=datetime.fromisoformat(row["last_interaction"]) if row["last_interaction"] else None,
                communication_style=style,
                relationship_score=row["relationship_score"],
                notes=row["notes"],
            )

        # Создать новый профиль
        cursor.execute("""
            INSERT INTO user_profiles 
            (account_id, user_id, username, interaction_count, last_interaction, 
             communication_style, relationship_score)
            VALUES (?, ?, ?, 0, ?, '{}', 0.5)
        """, (account_id, user_id, username, datetime.now()))
        profile_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return UserProfile(
            id=profile_id,
            account_id=account_id,
            user_id=user_id,
            username=username,
            interaction_count=0,
            last_interaction=datetime.now(),
            communication_style={},
            relationship_score=0.5,
        )

    def update_user_profile(self, profile: UserProfile):
        """Обновить профиль пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user_profiles 
            SET username = ?, interaction_count = ?, last_interaction = ?,
                communication_style = ?, relationship_score = ?, notes = ?
            WHERE account_id = ? AND user_id = ?
        """, (
            profile.username,
            profile.interaction_count,
            profile.last_interaction or datetime.now(),
            json.dumps(profile.communication_style),
            profile.relationship_score,
            profile.notes,
            profile.account_id,
            profile.user_id,
        ))
        conn.commit()
        conn.close()

    # === Topic Memory methods ===

    def get_or_create_topic_memory(self, account_id: int, topic_keyword: str) -> TopicMemory:
        """Получить или создать память о теме"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM topic_memory 
            WHERE account_id = ? AND topic_keyword = ?
        """, (account_id, topic_keyword))
        row = cursor.fetchone()

        if row:
            conn.close()
            return TopicMemory(
                id=row["id"],
                account_id=row["account_id"],
                topic_keyword=row["topic_keyword"],
                position=row["position"],
                priority=row["priority"],
                last_discussed=datetime.fromisoformat(row["last_discussed"]) if row["last_discussed"] else None,
                discussion_count=row["discussion_count"],
            )

        # Создать новую память
        cursor.execute("""
            INSERT INTO topic_memory 
            (account_id, topic_keyword, priority, last_discussed, discussion_count)
            VALUES (?, ?, 0.5, ?, 0)
        """, (account_id, topic_keyword, datetime.now()))
        topic_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return TopicMemory(
            id=topic_id,
            account_id=account_id,
            topic_keyword=topic_keyword,
            position=None,
            priority=0.5,
            last_discussed=datetime.now(),
            discussion_count=0,
        )

    def update_topic_memory(self, topic: TopicMemory):
        """Обновить память о теме"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE topic_memory 
            SET position = ?, priority = ?, last_discussed = ?, discussion_count = ?
            WHERE account_id = ? AND topic_keyword = ?
        """, (
            topic.position,
            topic.priority,
            topic.last_discussed or datetime.now(),
            topic.discussion_count,
            topic.account_id,
            topic.topic_keyword,
        ))
        conn.commit()
        conn.close()

    # === Interaction Log methods ===

    def log_interaction(self, interaction: InteractionLog) -> int:
        """Записать взаимодействие в лог"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interaction_log 
            (account_id, chat_id, action_type, message_id, response_text, 
             importance_score, decision_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction.account_id,
            interaction.chat_id,
            interaction.action_type,
            interaction.message_id,
            interaction.response_text,
            interaction.importance_score,
            interaction.decision_reason,
            interaction.timestamp or datetime.now(),
        ))
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return log_id

