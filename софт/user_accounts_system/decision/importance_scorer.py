"""
Расчет важности сообщения для принятия решения об ответе
"""

from typing import Dict, Any, Optional
from datetime import datetime, time

from ..listener.message_parser import MessageContext
from ..database.models import PersonalityProfile, UserProfile


class ImportanceScorer:
    """Расчет важности сообщения"""

    # Веса для различных факторов
    WEIGHTS = {
        "direct_mention": 0.3,
        "question": 0.15,
        "topic_relevance": 0.2,
        "user_relationship": 0.1,
        "tone_friendly": 0.1,
        "tone_argumentative": -0.3,
        "recent_activity": -0.2,
    }

    def __init__(self, profile: PersonalityProfile):
        self.profile = profile

    def calculate_score(
        self,
        context: MessageContext,
        analysis: Dict[str, Any],
        user_profile: Optional[UserProfile] = None,
        recent_responses_count: int = 0,
    ) -> float:
        """
        Рассчитать важность сообщения
        
        Args:
            context: Контекст сообщения
            analysis: Результаты анализа контекста
            user_profile: Профиль пользователя (опционально)
            recent_responses_count: Количество недавних ответов
            
        Returns:
            Оценка важности (0.0 - 1.0)
        """
        score = self.profile.base.activity_probability  # Базовая вероятность

        # Прямое упоминание
        if analysis.get("is_direct_mention"):
            score += self.WEIGHTS["direct_mention"]

        # Вопрос
        if analysis.get("is_question"):
            score += self.WEIGHTS["question"]

        # Релевантность темы
        topic_relevance = analysis.get("topic_relevance", 0.5)
        score += (topic_relevance - 0.5) * self.WEIGHTS["topic_relevance"]

        # Отношения с пользователем
        if user_profile:
            relationship = user_profile.relationship_score
            score += (relationship - 0.5) * self.WEIGHTS["user_relationship"]
        else:
            # Неизвестный пользователь - нейтральная оценка
            pass

        # Тон сообщения
        tone = analysis.get("tone", "neutral")
        if tone == "friendly":
            score += self.WEIGHTS["tone_friendly"]
        elif tone == "argumentative":
            score += self.WEIGHTS["tone_argumentative"]

        # Недавняя активность (штраф за частые ответы)
        if recent_responses_count > 0:
            penalty = min(recent_responses_count * 0.1, 0.5)
            score -= penalty

        # Проверка запрещенных тем/пользователей
        banned_check = analysis.get("banned_check", {})
        if banned_check.get("is_banned"):
            score = -1.0  # Гарантированно не отвечать

        # Ограничение диапазона
        score = max(0.0, min(1.0, score))

        return score

    def is_active_hours(self) -> bool:
        """Проверить, активны ли сейчас часы активности"""
        active_hours_config = self.profile.base.active_hours
        preferred = active_hours_config.get("preferred", [])
        
        if not preferred:
            return True  # Если не указано, всегда активно
        
        now = datetime.now()
        hour = now.hour
        
        # Упрощенная проверка (можно улучшить с учетом timezone)
        if "morning" in preferred and 6 <= hour < 12:
            return True
        if "afternoon" in preferred and 12 <= hour < 18:
            return True
        if "evening" in preferred and 18 <= hour < 22:
            return True
        if "night" in preferred and (22 <= hour or hour < 6):
            return True
        
        return False

