"""
Модуль интеграции с LLM для генерации ответов
"""

from .llm_service import LLMService
from .prompt_builder import PromptBuilder

__all__ = ["LLMService", "PromptBuilder"]

