"""
Менеджер задержек (cooldown) между ответами
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import random


class CooldownManager:
    """Управление задержками между ответами"""

    def __init__(self):
        # Последнее время ответа по чатам
        self.last_response_time: Dict[str, datetime] = {}
        
        # Минимальная задержка между ответами в одном чате (секунды)
        self.min_cooldown = 30
        
        # Максимальная задержка (для реалистичности)
        self.max_cooldown = 7200  # 2 часа

    def can_respond(self, chat_id: str, last_message_time: Optional[datetime] = None) -> bool:
        """
        Проверить, можно ли отвечать в чате
        
        Args:
            chat_id: ID чата
            last_message_time: Время последнего сообщения в чате
            
        Returns:
            True если можно отвечать
        """
        if chat_id not in self.last_response_time:
            return True
        
        last_response = self.last_response_time[chat_id]
        time_since_response = (datetime.now() - last_response).total_seconds()
        
        # Проверка минимальной задержки
        if time_since_response < self.min_cooldown:
            return False
        
        return True

    def get_response_delay(self, chat_id: str) -> float:
        """
        Получить задержку перед ответом (для реалистичности)
        
        Returns:
            Задержка в секундах
        """
        # Базовая задержка: 30 секунд - 2 часа
        # Используем логарифмическое распределение для более реалистичного поведения
        base_delay = random.uniform(30, 300)  # 30 сек - 5 мин (чаще)
        
        # Иногда большая задержка (10% случаев)
        if random.random() < 0.1:
            base_delay = random.uniform(1800, 7200)  # 30 мин - 2 часа
        
        # Учитываем, когда последний раз отвечали
        if chat_id in self.last_response_time:
            time_since = (datetime.now() - self.last_response_time[chat_id]).total_seconds()
            # Если недавно отвечали, увеличиваем задержку
            if time_since < 600:  # Меньше 10 минут
                base_delay *= 1.5
        
        return min(base_delay, self.max_cooldown)

    def record_response(self, chat_id: str):
        """Записать время ответа"""
        self.last_response_time[chat_id] = datetime.now()

    def reset_cooldown(self, chat_id: str):
        """Сбросить cooldown для чата"""
        if chat_id in self.last_response_time:
            del self.last_response_time[chat_id]

