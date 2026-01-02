"""
Сервис для работы с LLM
"""

import os
from typing import Optional, Dict, Any
import openai
from openai import OpenAI

# Альтернативные варианты:
# - Anthropic Claude API
# - Local LLM через Ollama
# - Hugging Face API


class LLMService:
    """Сервис для генерации ответов через LLM"""

    def __init__(
        self,
        provider: str = "openai",  # "openai", "anthropic", "ollama", "huggingface"
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,  # Для Ollama или других
    ):
        """
        Args:
            provider: Провайдер LLM
            api_key: API ключ
            model: Модель для использования
            base_url: Базовый URL (для локальных моделей)
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        
        if provider == "openai":
            self.client = OpenAI(api_key=self.api_key)
        elif provider == "ollama":
            self.client = OpenAI(api_key="ollama", base_url=base_url or "http://localhost:11434/v1")
        else:
            self.client = None

    def generate_response(self, prompt: str, max_tokens: int = 200) -> str:
        """
        Сгенерировать ответ на основе промпта
        
        Args:
            prompt: Промпт для генерации
            max_tokens: Максимальное количество токенов
            
        Returns:
            Сгенерированный текст
        """
        if not self.client:
            return "LLM service not configured"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.8,  # Для разнообразия ответов
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Извини, не могу ответить сейчас."

    def generate_with_context(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[list] = None,
        max_tokens: int = 200,
    ) -> str:
        """
        Сгенерировать ответ с учетом истории диалога
        
        Args:
            system_prompt: Системный промпт
            user_message: Сообщение пользователя
            conversation_history: История диалога
            max_tokens: Максимальное количество токенов
            
        Returns:
            Сгенерированный текст
        """
        if not self.client:
            return "LLM service not configured"
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Добавить историю
        if conversation_history:
            messages.extend(conversation_history)
        
        # Добавить текущее сообщение
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.8,
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Извини, не могу ответить сейчас."

