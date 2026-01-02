"""
Движок эволюции личности
"""

from typing import Dict, Any, Optional
from datetime import datetime

from ..database.db_manager import DatabaseManager
from ..database.models import PersonalityProfile, DynamicPersonalityConfig


class EvolutionEngine:
    """Движок для эволюции личности на основе опыта"""

    # Скорость изменения параметров (медленные изменения)
    EVOLUTION_RATE = 0.02  # 2% за событие
    MAX_CHANGE = 0.05  # Максимальное изменение за раз

    def __init__(self, account_id: int, db_manager: DatabaseManager):
        self.account_id = account_id
        self.db = db_manager

    def evolve_from_interaction(
        self,
        profile: PersonalityProfile,
        interaction_type: str,  # "responded", "ignored", "discussion", "positive_reaction"
        context: Dict[str, Any] = None,
    ) -> PersonalityProfile:
        """
        Эволюционировать личность на основе взаимодействия
        
        Args:
            profile: Текущий профиль
            interaction_type: Тип взаимодействия
            context: Дополнительный контекст
            
        Returns:
            Обновленный профиль
        """
        if not profile.constraints.evolution_enabled:
            return profile
        
        if profile.constraints.personality_locked:
            return profile
        
        dynamic = profile.dynamic
        changes = []
        
        # Эволюция на основе типа взаимодействия
        if interaction_type == "responded":
            # Если ответили, увеличиваем активность
            old_activity = dynamic.activity_level
            dynamic.activity_level = min(1.0, old_activity + self.EVOLUTION_RATE)
            if abs(dynamic.activity_level - old_activity) > 0.001:
                changes.append(("activity_level", old_activity, dynamic.activity_level))
        
        elif interaction_type == "discussion":
            # Если участвовали в дискуссии, увеличиваем склонность к обсуждениям
            old_discussion = dynamic.discussion_tendency
            dynamic.discussion_tendency = min(1.0, old_discussion + self.EVOLUTION_RATE * 2)
            if abs(dynamic.discussion_tendency - old_discussion) > 0.001:
                changes.append(("discussion_tendency", old_discussion, dynamic.discussion_tendency))
        
        elif interaction_type == "positive_reaction":
            # Положительная реакция - увеличиваем активность
            old_activity = dynamic.activity_level
            dynamic.activity_level = min(1.0, old_activity + self.EVOLUTION_RATE * 1.5)
            if abs(dynamic.activity_level - old_activity) > 0.001:
                changes.append(("activity_level", old_activity, dynamic.activity_level))
        
        elif interaction_type == "ignored":
            # Если игнорировали, немного снижаем активность
            old_activity = dynamic.activity_level
            dynamic.activity_level = max(0.0, old_activity - self.EVOLUTION_RATE * 0.5)
            if abs(dynamic.activity_level - old_activity) > 0.001:
                changes.append(("activity_level", old_activity, dynamic.activity_level))
        
        # Эволюция приоритетов тем
        if context and "topic_keywords" in context:
            for keyword in context.get("topic_keywords", []):
                if keyword not in dynamic.topic_priorities:
                    dynamic.topic_priorities[keyword] = 0.5
                
                # Увеличить приоритет темы
                old_priority = dynamic.topic_priorities[keyword]
                dynamic.topic_priorities[keyword] = min(
                    1.0,
                    old_priority + self.EVOLUTION_RATE
                )
                
                if abs(dynamic.topic_priorities[keyword] - old_priority) > 0.001:
                    changes.append(
                        (f"topic_priority_{keyword}", old_priority, dynamic.topic_priorities[keyword])
                    )
        
        # Эволюция отношений с пользователями
        if context and "user_id" in context:
            user_id = context["user_id"]
            if user_id not in dynamic.user_relationships:
                dynamic.user_relationships[user_id] = 0.5
            
            # Если был положительный опыт, улучшаем отношения
            if interaction_type in ["responded", "positive_reaction"]:
                old_relationship = dynamic.user_relationships[user_id]
                dynamic.user_relationships[user_id] = min(
                    1.0,
                    old_relationship + self.EVOLUTION_RATE
                )
                
                if abs(dynamic.user_relationships[user_id] - old_relationship) > 0.001:
                    changes.append(
                        (f"user_relationship_{user_id}", old_relationship, dynamic.user_relationships[user_id])
                    )
        
        # Сохранить изменения в БД
        if changes:
            profile.last_updated = datetime.now()
            self.db.save_personality_profile(profile)
            
            # Записать в историю эволюции
            self._log_evolution(changes, interaction_type)
        
        return profile

    def _log_evolution(self, changes: list, reason: str):
        """Записать изменения в историю эволюции"""
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for param_name, old_value, new_value in changes:
            cursor.execute("""
                INSERT INTO evolution_history 
                (account_id, parameter_name, old_value, new_value, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (self.account_id, param_name, old_value, new_value, reason))
        
        conn.commit()
        conn.close()

