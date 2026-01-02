"""
Менеджер памяти для аккаунта
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..database.db_manager import DatabaseManager
from ..database.models import (
    ChatMessage,
    UserProfile,
    TopicMemory,
    InteractionLog,
)
from ..listener.message_parser import MessageContext


class MemoryManager:
    """Центральный менеджер памяти для аккаунта"""

    def __init__(self, account_id: int, db_manager: DatabaseManager):
        self.account_id = account_id
        self.db = db_manager
        
        # Кэш для быстрого доступа
        self._chat_cache: Dict[str, List[ChatMessage]] = {}
        self._user_cache: Dict[str, UserProfile] = {}
        self._topic_cache: Dict[str, TopicMemory] = {}

    # === Chat Memory ===

    def save_message(self, context: MessageContext):
        """Сохранить сообщение в память"""
        message = ChatMessage(
            account_id=self.account_id,
            chat_id=context.chat_id,
            message_id=context.message_id,
            user_id=context.user_id,
            username=context.username,
            message_text=context.text,
            timestamp=datetime.now(),
            is_reply_to=context.reply_to_message_id,
            context_data={
                "tone": context.tone,
                "is_question": context.is_question,
                "topic_keywords": context.topic_keywords,
                "mentions": context.mentions,
            },
        )
        
        self.db.save_chat_message(message)
        
        # Обновить кэш
        if context.chat_id not in self._chat_cache:
            self._chat_cache[context.chat_id] = []
        self._chat_cache[context.chat_id].append(message)
        
        # Ограничить размер кэша
        if len(self._chat_cache[context.chat_id]) > 100:
            self._chat_cache[context.chat_id] = self._chat_cache[context.chat_id][-100:]

    def get_chat_history(self, chat_id: str, limit: int = 50) -> List[ChatMessage]:
        """Получить историю чата"""
        # Проверить кэш
        if chat_id in self._chat_cache and len(self._chat_cache[chat_id]) >= limit:
            return self._chat_cache[chat_id][-limit:]
        
        # Загрузить из БД
        history = self.db.get_chat_history(self.account_id, chat_id, limit)
        
        # Обновить кэш
        self._chat_cache[chat_id] = history
        
        return history

    def get_recent_messages_count(self, chat_id: str, minutes: int = 60) -> int:
        """Получить количество сообщений за последние N минут"""
        history = self.get_chat_history(chat_id, limit=100)
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        return sum(1 for msg in history if msg.timestamp and msg.timestamp >= cutoff)

    # === User Memory ===

    def get_user_profile(self, user_id: str, username: Optional[str] = None) -> UserProfile:
        """Получить профиль пользователя"""
        # Проверить кэш
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        
        # Загрузить из БД
        profile = self.db.get_or_create_user_profile(self.account_id, user_id, username)
        
        # Обновить кэш
        self._user_cache[user_id] = profile
        
        return profile

    def update_user_interaction(self, user_id: str, context: MessageContext, 
                                response_sent: bool = False):
        """Обновить информацию о взаимодействии с пользователем"""
        profile = self.get_user_profile(user_id, context.username)
        
        profile.interaction_count += 1
        profile.last_interaction = datetime.now()
        
        # Обновить стиль общения
        if context.tone not in profile.communication_style:
            profile.communication_style[context.tone] = 0
        profile.communication_style[context.tone] += 1
        
        # Обновить оценку отношений (упрощенная логика)
        if response_sent:
            # Если ответили, отношения улучшаются
            profile.relationship_score = min(1.0, profile.relationship_score + 0.05)
        else:
            # Если не ответили, отношения немного ухудшаются
            profile.relationship_score = max(0.0, profile.relationship_score - 0.02)
        
        self.db.update_user_profile(profile)
        self._user_cache[user_id] = profile

    # === Topic Memory ===

    def get_topic_memory(self, topic_keyword: str) -> TopicMemory:
        """Получить память о теме"""
        # Проверить кэш
        if topic_keyword in self._topic_cache:
            return self._topic_cache[topic_keyword]
        
        # Загрузить из БД
        topic = self.db.get_or_create_topic_memory(self.account_id, topic_keyword)
        
        # Обновить кэш
        self._topic_cache[topic_keyword] = topic
        
        return topic

    def update_topic_discussion(self, topic_keyword: str, position: Optional[str] = None):
        """Обновить информацию о обсуждении темы"""
        topic = self.get_topic_memory(topic_keyword)
        
        topic.discussion_count += 1
        topic.last_discussed = datetime.now()
        
        if position:
            topic.position = position
        
        # Увеличить приоритет темы
        topic.priority = min(1.0, topic.priority + 0.1)
        
        self.db.update_topic_memory(topic)
        self._topic_cache[topic_keyword] = topic

    # === Context Building ===

    def build_context_for_llm(self, chat_id: str, limit: int = 20) -> Dict[str, Any]:
        """Построить контекст для LLM"""
        history = self.get_chat_history(chat_id, limit)
        
        # Форматировать историю
        formatted_history = []
        for msg in history[-limit:]:
            formatted_history.append({
                "user": msg.username or msg.user_id,
                "text": msg.message_text,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            })
        
        return {
            "chat_history": formatted_history,
            "message_count": len(history),
        }

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Получить контекст о пользователе"""
        profile = self.get_user_profile(user_id)
        
        return {
            "username": profile.username,
            "interaction_count": profile.interaction_count,
            "relationship_score": profile.relationship_score,
            "communication_style": profile.communication_style,
            "last_interaction": profile.last_interaction.isoformat() if profile.last_interaction else None,
        }

    def get_topic_context(self, topic_keywords: List[str]) -> Dict[str, Any]:
        """Получить контекст о темах"""
        topics = {}
        for keyword in topic_keywords:
            topic = self.get_topic_memory(keyword)
            topics[keyword] = {
                "position": topic.position,
                "priority": topic.priority,
                "discussion_count": topic.discussion_count,
            }
        
        return topics

    # === Interaction Logging ===

    def log_interaction(self, chat_id: str, action_type: str, 
                       message_id: Optional[int] = None,
                       response_text: Optional[str] = None,
                       importance_score: Optional[float] = None,
                       decision_reason: Optional[str] = None):
        """Записать взаимодействие в лог"""
        from ..database.models import InteractionLog
        
        interaction = InteractionLog(
            account_id=self.account_id,
            chat_id=chat_id,
            action_type=action_type,
            message_id=message_id,
            response_text=response_text,
            importance_score=importance_score,
            decision_reason=decision_reason,
        )
        
        self.db.log_interaction(interaction)

