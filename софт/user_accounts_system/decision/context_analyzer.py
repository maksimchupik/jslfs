"""
Анализатор контекста сообщения
"""

from typing import Dict, Any
from datetime import datetime

from ..listener.message_parser import MessageContext
from ..database.models import PersonalityProfile


class ContextAnalyzer:
    """Анализ контекста сообщения для принятия решения"""

    def __init__(self, profile: PersonalityProfile):
        self.profile = profile

    def analyze(self, context: MessageContext, chat_history_count: int = 0) -> Dict[str, Any]:
        """
        Проанализировать контекст сообщения
        
        Args:
            context: Контекст сообщения
            chat_history_count: Количество сообщений в истории чата
            
        Returns:
            Словарь с результатами анализа
        """
        analysis = {
            "is_direct_mention": context.is_direct_mention,
            "is_question": context.is_question,
            "tone": context.tone,
            "is_reply": context.is_reply,
            "topic_relevance": 0.0,
            "chat_activity": self._analyze_chat_activity(chat_history_count),
            "user_relationship": 0.5,  # Будет заполнено из памяти
            "banned_check": self._check_banned(context),
        }

        # Релевантность темы
        analysis["topic_relevance"] = self._calculate_topic_relevance(context)

        return analysis

    def _analyze_chat_activity(self, history_count: int) -> str:
        """Проанализировать активность в чате"""
        if history_count == 0:
            return "quiet"
        elif history_count < 5:
            return "low"
        elif history_count < 20:
            return "moderate"
        else:
            return "high"

    def _calculate_topic_relevance(self, context: MessageContext) -> float:
        """Рассчитать релевантность темы"""
        if not context.topic_keywords:
            return 0.5  # Нейтральная релевантность
        
        # Проверка интересов из профиля
        interests = self.profile.base.interests
        if not interests:
            return 0.5
        
        # Простая проверка совпадения ключевых слов
        text_lower = context.text.lower()
        for interest in interests:
            if interest.lower() in text_lower:
                return 0.8  # Высокая релевантность
        
        # Проверка приоритетов тем
        topic_priorities = self.profile.dynamic.topic_priorities
        for keyword in context.topic_keywords:
            if keyword in topic_priorities:
                return topic_priorities[keyword]
        
        return 0.5

    def _check_banned(self, context: MessageContext) -> Dict[str, bool]:
        """Проверить запрещенные темы и пользователей"""
        banned_topics = self.profile.constraints.banned_topics
        banned_users = self.profile.constraints.banned_users
        
        text_lower = context.text.lower()
        
        topic_banned = any(
            banned_topic.lower() in text_lower 
            for banned_topic in banned_topics
        )
        
        user_banned = context.user_id in banned_users or (
            context.username and context.username in banned_users
        )
        
        return {
            "topic_banned": topic_banned,
            "user_banned": user_banned,
            "is_banned": topic_banned or user_banned,
        }

