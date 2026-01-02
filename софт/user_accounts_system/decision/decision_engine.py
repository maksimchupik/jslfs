"""
Движок принятия решений о ответах
"""

from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass

from ..listener.message_parser import MessageContext
from ..database.models import PersonalityProfile, UserProfile
from .context_analyzer import ContextAnalyzer
from .importance_scorer import ImportanceScorer
from .cooldown_manager import CooldownManager


class DecisionType(Enum):
    """Тип решения"""
    RESPOND = "respond"  # Ответить
    REACT = "react"  # Отреагировать (если поддерживается)
    IGNORE = "ignore"  # Игнорировать
    DEFER = "defer"  # Отложить (не активные часы)


@dataclass
class Decision:
    """Решение о действии"""
    decision_type: DecisionType
    importance_score: float
    reason: str
    delay: Optional[float] = None  # Задержка перед действием (секунды)


class DecisionEngine:
    """Движок принятия решений"""

    # Пороги для принятия решений
    RESPOND_THRESHOLD = 0.5  # Порог для ответа
    REACT_THRESHOLD = 0.3  # Порог для реакции

    def __init__(self, profile: PersonalityProfile):
        self.profile = profile
        self.context_analyzer = ContextAnalyzer(profile)
        self.importance_scorer = ImportanceScorer(profile)
        self.cooldown_manager = CooldownManager()

    def make_decision(
        self,
        context: MessageContext,
        chat_history_count: int = 0,
        user_profile: Optional[UserProfile] = None,
        recent_responses_count: int = 0,
    ) -> Decision:
        """
        Принять решение о действии
        
        Args:
            context: Контекст сообщения
            chat_history_count: Количество сообщений в истории
            user_profile: Профиль пользователя
            recent_responses_count: Количество недавних ответов
            
        Returns:
            Decision с решением
        """
        # Проверка разрешенных чатов
        allowed_chats = self.profile.constraints.allowed_chats
        if allowed_chats and context.chat_id not in allowed_chats:
            return Decision(
                decision_type=DecisionType.IGNORE,
                importance_score=-1.0,
                reason=f"Chat {context.chat_id} not in allowed chats list",
            )

        # Проверка ограничений автономности
        if self.profile.constraints.autonomy_level < 0.1:
            return Decision(
                decision_type=DecisionType.IGNORE,
                importance_score=0.0,
                reason="Low autonomy level - manual control required",
            )

        # Анализ контекста
        analysis = self.context_analyzer.analyze(context, chat_history_count)

        # Проверка запрещенных тем/пользователей
        banned_check = analysis.get("banned_check", {})
        if banned_check.get("is_banned"):
            return Decision(
                decision_type=DecisionType.IGNORE,
                importance_score=-1.0,
                reason=f"Banned: topic={banned_check.get('topic_banned')}, user={banned_check.get('user_banned')}",
            )

        # Проверка активных часов
        if not self.importance_scorer.is_active_hours():
            return Decision(
                decision_type=DecisionType.DEFER,
                importance_score=0.0,
                reason="Outside active hours",
            )

        # Проверка cooldown
        if not self.cooldown_manager.can_respond(context.chat_id):
            return Decision(
                decision_type=DecisionType.IGNORE,
                importance_score=0.0,
                reason="Cooldown period - too soon after last response",
            )

        # Расчет важности
        importance_score = self.importance_scorer.calculate_score(
            context,
            analysis,
            user_profile,
            recent_responses_count,
        )

        # Принятие решения
        if importance_score >= self.RESPOND_THRESHOLD:
            delay = self.cooldown_manager.get_response_delay(context.chat_id)
            self.cooldown_manager.record_response(context.chat_id)
            
            return Decision(
                decision_type=DecisionType.RESPOND,
                importance_score=importance_score,
                reason=f"High importance: {importance_score:.2f}",
                delay=delay,
            )
        elif importance_score >= self.REACT_THRESHOLD:
            return Decision(
                decision_type=DecisionType.REACT,
                importance_score=importance_score,
                reason=f"Medium importance: {importance_score:.2f}",
            )
        else:
            return Decision(
                decision_type=DecisionType.IGNORE,
                importance_score=importance_score,
                reason=f"Low importance: {importance_score:.2f}",
            )

