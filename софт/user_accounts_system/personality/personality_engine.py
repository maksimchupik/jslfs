"""
Движок управления личностью
"""

from typing import Optional, Dict, List, Any

from ..database.db_manager import DatabaseManager
from ..database.models import PersonalityProfile, BasePersonalityConfig, DynamicPersonalityConfig, PersonalityConstraints
from .evolution_engine import EvolutionEngine


class PersonalityEngine:
    """Движок для управления и применения личности"""

    def __init__(self, account_id: int, db_manager: DatabaseManager):
        self.account_id = account_id
        self.db = db_manager
        self.evolution_engine = EvolutionEngine(account_id, db_manager)
        self._profile: Optional[PersonalityProfile] = None

    def load_profile(self) -> PersonalityProfile:
        """Загрузить профиль личности"""
        profile = self.db.get_personality_profile(self.account_id)
        
        if not profile:
            # Создать профиль по умолчанию
            profile = self._create_default_profile()
            self.db.save_personality_profile(profile)
        
        self._profile = profile
        return profile

    def get_profile(self) -> PersonalityProfile:
        """Получить текущий профиль (загружает если нужно)"""
        if not self._profile:
            return self.load_profile()
        return self._profile

    def update_base_config(self, base_config: Dict[str, Any]) -> PersonalityProfile:
        """Обновить базовую конфигурацию личности"""
        profile = self.get_profile()
        
        if profile.constraints.personality_locked:
            raise ValueError("Personality is locked and cannot be modified")
        
        # Обновить базовые параметры
        for key, value in base_config.items():
            if hasattr(profile.base, key):
                setattr(profile.base, key, value)
        
        self.db.save_personality_profile(profile)
        self._profile = profile
        return profile

    def update_constraints(self, constraints: Dict[str, Any]) -> PersonalityProfile:
        """Обновить ограничения"""
        profile = self.get_profile()

        for key, value in constraints.items():
            if hasattr(profile.constraints, key):
                setattr(profile.constraints, key, value)

        self.db.save_personality_profile(profile)
        self._profile = profile
        return profile

    def update_allowed_chats(self, allowed_chats: List[str]) -> PersonalityProfile:
        """Обновить список разрешенных чатов"""
        profile = self.get_profile()

        if profile.constraints.personality_locked:
            raise ValueError("Personality is locked and cannot be modified")

        profile.constraints.allowed_chats = allowed_chats
        self.db.save_personality_profile(profile)
        self._profile = profile
        return profile

    def lock_personality(self) -> PersonalityProfile:
        """Заблокировать личность от изменений"""
        profile = self.get_profile()
        profile.constraints.personality_locked = True
        self.db.save_personality_profile(profile)
        self._profile = profile
        return profile

    def unlock_personality(self) -> PersonalityProfile:
        """Разблокировать личность"""
        profile = self.get_profile()
        profile.constraints.personality_locked = False
        self.db.save_personality_profile(profile)
        self._profile = profile
        return profile

    def evolve_from_interaction(
        self,
        interaction_type: str,
        context: Dict[str, Any] = None,
    ) -> PersonalityProfile:
        """Эволюционировать личность на основе взаимодействия"""
        profile = self.get_profile()
        updated_profile = self.evolution_engine.evolve_from_interaction(
            profile,
            interaction_type,
            context,
        )
        self._profile = updated_profile
        return updated_profile

    def _create_default_profile(self) -> PersonalityProfile:
        """Создать профиль по умолчанию"""
        base = BasePersonalityConfig(
            speech_style="дружелюбный",
            message_length="средний",
            emoji_usage="редко",
            interests=["IT", "технологии"],
            active_hours={
                "preferred": ["evening", "night"],
                "timezone": "UTC+3",
            },
            activity_probability=0.35,
            custom_prompt="",
        )
        
        dynamic = DynamicPersonalityConfig(
            discussion_tendency=0.5,
            activity_level=0.5,
            topic_priorities={},
            user_relationships={},
        )
        
        constraints = PersonalityConstraints(
            personality_locked=False,
            evolution_enabled=True,
            autonomy_level=0.8,
            banned_topics=[],
            banned_users=[],
        )
        
        return PersonalityProfile(
            account_id=self.account_id,
            base=base,
            dynamic=dynamic,
            constraints=constraints,
        )

