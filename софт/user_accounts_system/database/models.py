"""
Модели базы данных для системы управления аккаунтами
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class Account:
    """Модель аккаунта"""
    id: Optional[int] = None
    phone_number: str = ""
    session_file: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    # Добавляем поля для хранения данных для подключения
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    session_string: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "session_file": self.session_file,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "api_id": self.api_id,
            "api_hash": self.api_hash,
            "session_string": self.session_string,
        }


@dataclass
class BasePersonalityConfig:
    """Базовые параметры личности (задаются вручную)"""
    speech_style: str = "дружелюбный"  # ироничный | формальный | дружелюбный
    message_length: str = "средний"  # короткий | средний | развернутый
    emoji_usage: str = "редко"  # никогда | редко | часто
    interests: List[str] = None
    active_hours: Dict[str, Any] = None
    activity_probability: float = 0.35
    custom_prompt: str = ""  # Пользовательский промпт

    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.active_hours is None:
            self.active_hours = {
                "preferred": ["evening", "night"],
                "timezone": "UTC+3"
            }

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DynamicPersonalityConfig:
    """Динамические параметры личности (эволюционируют)"""
    discussion_tendency: float = 0.5  # 0.0 - избегает споров, 1.0 - любит спорить
    activity_level: float = 0.5  # 0.0 - пассивный, 1.0 - очень активный
    topic_priorities: Dict[str, float] = None  # тема -> приоритет (0.0-1.0)
    user_relationships: Dict[str, float] = None  # user_id -> отношение (0.0-1.0)

    def __post_init__(self):
        if self.topic_priorities is None:
            self.topic_priorities = {}
        if self.user_relationships is None:
            self.user_relationships = {}

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PersonalityConstraints:
    """Ограничения и настройки личности"""
    personality_locked: bool = False  # Заблокирована ли личность от изменений
    evolution_enabled: bool = True  # Включено ли развитие
    autonomy_level: float = 0.8  # 0.0 - полный контроль, 1.0 - полная автономность
    banned_topics: List[str] = None  # Запрещенные темы
    banned_users: List[str] = None  # Запрещенные пользователи
    allowed_chats: List[str] = None  # Разрешенные чаты (если пустой список - все разрешены)

    def __post_init__(self):
        if self.banned_topics is None:
            self.banned_topics = []
        if self.banned_users is None:
            self.banned_users = []
        if self.allowed_chats is None:
            self.allowed_chats = []

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PersonalityProfile:
    """Полный профиль личности"""
    account_id: int
    base: BasePersonalityConfig
    dynamic: DynamicPersonalityConfig
    constraints: PersonalityConstraints
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "account_id": self.account_id,
            "base": self.base.to_dict(),
            "dynamic": self.dynamic.to_dict(),
            "constraints": self.constraints.to_dict(),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PersonalityProfile":
        base = BasePersonalityConfig(**data.get("base", {}))
        dynamic = DynamicPersonalityConfig(**data.get("dynamic", {}))
        constraints = PersonalityConstraints(**data.get("constraints", {}))
        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])
        
        return cls(
            account_id=data["account_id"],
            base=base,
            dynamic=dynamic,
            constraints=constraints,
            last_updated=last_updated
        )


@dataclass
class ChatMessage:
    """Модель сообщения в чате"""
    id: Optional[int] = None
    account_id: int = 0
    chat_id: str = ""
    message_id: Optional[int] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    message_text: str = ""
    timestamp: Optional[datetime] = None
    is_reply_to: Optional[int] = None
    context_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.context_data is None:
            self.context_data = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "chat_id": self.chat_id,
            "message_id": self.message_id,
            "user_id": self.user_id,
            "username": self.username,
            "message_text": self.message_text,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_reply_to": self.is_reply_to,
            "context_data": self.context_data,
        }


@dataclass
class UserProfile:
    """Профиль пользователя для памяти"""
    id: Optional[int] = None
    account_id: int = 0
    user_id: str = ""
    username: Optional[str] = None
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None
    communication_style: Dict[str, Any] = None
    relationship_score: float = 0.5  # 0.0 - негативное, 1.0 - позитивное
    notes: Optional[str] = None

    def __post_init__(self):
        if self.communication_style is None:
            self.communication_style = {}

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "user_id": self.user_id,
            "username": self.username,
            "interaction_count": self.interaction_count,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "communication_style": self.communication_style,
            "relationship_score": self.relationship_score,
            "notes": self.notes,
        }


@dataclass
class TopicMemory:
    """Память о теме обсуждения"""
    id: Optional[int] = None
    account_id: int = 0
    topic_keyword: str = ""
    position: Optional[str] = None  # Позиция по теме
    priority: float = 0.5  # Приоритет темы (0.0-1.0)
    last_discussed: Optional[datetime] = None
    discussion_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "topic_keyword": self.topic_keyword,
            "position": self.position,
            "priority": self.priority,
            "last_discussed": self.last_discussed.isoformat() if self.last_discussed else None,
            "discussion_count": self.discussion_count,
        }


@dataclass
class InteractionLog:
    """Лог взаимодействий"""
    id: Optional[int] = None
    account_id: int = 0
    chat_id: str = ""
    action_type: str = ""  # 'message', 'reaction', 'ignore'
    message_id: Optional[int] = None
    response_text: Optional[str] = None
    importance_score: Optional[float] = None
    decision_reason: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "chat_id": self.chat_id,
            "action_type": self.action_type,
            "message_id": self.message_id,
            "response_text": self.response_text,
            "importance_score": self.importance_score,
            "decision_reason": self.decision_reason,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

