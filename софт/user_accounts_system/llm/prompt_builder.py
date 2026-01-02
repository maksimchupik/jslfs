"""
Построитель промптов для LLM
"""

from typing import List, Dict, Any
from datetime import datetime

from ..database.models import PersonalityProfile
from ..listener.message_parser import MessageContext


class PromptBuilder:
    """Построитель промптов для генерации ответов"""

    def __init__(self, profile: PersonalityProfile):
        self.profile = profile

    def build_prompt(
        self,
        context: MessageContext,
        chat_history: List[Dict[str, Any]],
        user_context: Dict[str, Any] = None,
        topic_context: Dict[str, Any] = None,
    ) -> str:
        """
        Построить промпт для LLM
        
        Args:
            context: Контекст текущего сообщения
            chat_history: История чата (форматированная)
            user_context: Контекст о пользователе
            topic_context: Контекст о темах
            
        Returns:
            Готовый промпт
        """
        # Системный промпт
        system_prompt = self._build_system_prompt()
        
        # Контекст диалога
        dialogue_context = self._build_dialogue_context(chat_history, context)
        
        # Память о пользователе
        memory_context = self._build_memory_context(user_context, topic_context)
        
        # Инструкции
        instructions = self._build_instructions(context)
        
        # Объединить все части
        full_prompt = f"""{system_prompt}

{memory_context}

{dialogue_context}

{instructions}"""

        return full_prompt

    def _build_system_prompt(self) -> str:
        """Построить системный промпт"""
        base = self.profile.base

        # Если задан пользовательский промпт, используем его
        if base.custom_prompt:
            return base.custom_prompt

        # Описание стиля
        style_desc = {
            "ироничный": "ироничный, с сарказмом, но дружелюбный",
            "формальный": "формальный, вежливый, профессиональный",
            "дружелюбный": "дружелюбный, открытый, теплый",
        }.get(base.speech_style, base.speech_style)

        # Описание длины
        length_desc = {
            "короткий": "1-2 предложения, кратко",
            "средний": "2-4 предложения, развернуто",
            "развернутый": "4+ предложений, подробно",
        }.get(base.message_length, base.message_length)

        # Описание эмодзи
        emoji_desc = {
            "никогда": "не используй эмодзи",
            "редко": "используй эмодзи очень редко, только когда уместно",
            "часто": "используй эмодзи часто, для выражения эмоций",
        }.get(base.emoji_usage, base.emoji_usage)

        interests_str = ", ".join(base.interests) if base.interests else "разные темы"

        return f"""Ты — человек со следующими характеристиками:
- Стиль общения: {style_desc}
- Длина сообщений: {length_desc}
- Использование эмодзи: {emoji_desc}
- Интересы: {interests_str}

Веди себя естественно, как живой человек. Не повторяй предыдущие мысли. Будь контекстным и уместным."""

    def _build_dialogue_context(
        self,
        chat_history: List[Dict[str, Any]],
        current_context: MessageContext,
    ) -> str:
        """Построить контекст диалога"""
        if not chat_history:
            return f"Новое сообщение в чате:\n{current_context.user_id}: {current_context.text}"
        
        # Форматировать историю
        history_lines = []
        for msg in chat_history[-10:]:  # Последние 10 сообщений
            user = msg.get("user", "Unknown")
            text = msg.get("text", "")
            history_lines.append(f"{user}: {text}")
        
        history_text = "\n".join(history_lines)
        
        return f"""Контекст диалога (последние сообщения):
{history_text}

Текущее сообщение:
{current_context.username or current_context.user_id}: {current_context.text}"""

    def _build_memory_context(
        self,
        user_context: Dict[str, Any] = None,
        topic_context: Dict[str, Any] = None,
    ) -> str:
        """Построить контекст памяти"""
        memory_parts = []
        
        if user_context:
            username = user_context.get("username", "пользователь")
            interaction_count = user_context.get("interaction_count", 0)
            relationship = user_context.get("relationship_score", 0.5)
            
            if interaction_count > 0:
                relationship_desc = "хорошие" if relationship > 0.6 else "нейтральные" if relationship > 0.4 else "напряженные"
                memory_parts.append(
                    f"Ты общался с {username} {interaction_count} раз(а). "
                    f"У вас {relationship_desc} отношения."
                )
        
        if topic_context:
            for topic, info in topic_context.items():
                position = info.get("position")
                if position:
                    memory_parts.append(f"По теме '{topic}' ты ранее высказывал позицию: {position}")
        
        if memory_parts:
            return "Память:\n" + "\n".join(memory_parts)
        
        return ""

    def _build_instructions(self, context: MessageContext) -> str:
        """Построить инструкции для ответа"""
        instructions = []
        
        # Учет тона
        if context.tone == "argumentative":
            instructions.append("Сообщение имеет спорный тон. Будь дипломатичным, но можешь высказать свое мнение.")
        elif context.tone == "friendly":
            instructions.append("Сообщение дружелюбное. Отвечай в том же тоне.")
        elif context.tone == "humorous":
            instructions.append("В диалоге есть юмор. Можешь ответить с легкой иронией или шуткой.")
        
        # Учет вопроса
        if context.is_question:
            instructions.append("Это вопрос. Дай содержательный ответ.")
        
        # Учет reply
        if context.is_reply:
            instructions.append("Это ответ на твое сообщение. Учти контекст предыдущего обсуждения.")
        
        # Динамические параметры
        dynamic = self.profile.dynamic
        if dynamic.discussion_tendency > 0.7:
            instructions.append("Ты склонен к дискуссиям. Можешь высказать свое мнение более активно.")
        elif dynamic.discussion_tendency < 0.3:
            instructions.append("Ты избегаешь споров. Будь более нейтральным.")
        
        if instructions:
            return "Инструкции:\n" + "\n".join(f"- {inst}" for inst in instructions)
        
        return "Ответь на сообщение естественно и уместно."

