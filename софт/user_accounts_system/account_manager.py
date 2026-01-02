"""
Менеджер аккаунта - основной orchestrator для одного аккаунта
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from .database.db_manager import DatabaseManager
from .database.models import Account
from .listener.message_listener import MessageListener
from .listener.message_parser import MessageContext
from .decision.decision_engine import DecisionEngine, DecisionType, Decision
from .memory.memory_manager import MemoryManager
from .personality.personality_engine import PersonalityEngine
from .llm.llm_service import LLMService
from .llm.prompt_builder import PromptBuilder


class AccountManager:
    """Менеджер для управления одним аккаунтом"""

    def __init__(
        self,
        account_id: int,
        api_id: int,
        api_hash: str,
        session_string: str,
        db_manager: DatabaseManager,
        llm_service: LLMService,
    ):
        """
        Args:
            account_id: ID аккаунта в БД
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_string: Сессия в формате StringSession
            db_manager: Менеджер БД
            llm_service: Сервис LLM
        """
        self.account_id = account_id
        self.db = db_manager
        self.llm_service = llm_service
        
        # Инициализация компонентов
        self.personality_engine = PersonalityEngine(account_id, db_manager)
        self.memory_manager = MemoryManager(account_id, db_manager)
        
        # Загрузить профиль
        self.profile = self.personality_engine.load_profile()
        self.decision_engine = DecisionEngine(self.profile)
        
        # Инициализация listener
        account = self.db.get_account(account_id)
        self.listener = MessageListener(
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
            account_username=None,  # Будет загружено после старта
        )
        
        # Prompt builder
        self.prompt_builder = PromptBuilder(self.profile)
        
        # Статистика
        self.stats = {
            "messages_received": 0,
            "messages_responded": 0,
            "messages_ignored": 0,
            "last_activity": None,
        }

    async def start(self):
        """Запустить аккаунт"""
        # Проверить действительность сессии перед запуском
        try:
            await self.listener.start()

            # Попробовать получить информацию об аккаунте для проверки сессии
            me = await self.listener.client.get_me()
            if me:
                # Обновить статус аккаунта в базе данных на активный
                account = self.db.get_account(self.account_id)
                if account:
                    account.is_active = True
                    self.db.update_account(account)

                self.listener.account_username = me.username
                self.listener.parser.account_username = me.username
                print(f"Account {self.account_id} started successfully")
            else:
                # Если не удалось получить информацию, сессия недействительна
                print(f"Account {self.account_id} has invalid session")
                # Обновить статус аккаунта в базе данных на неактивный
                account = self.db.get_account(self.account_id)
                if account:
                    account.is_active = False
                    self.db.update_account(account)
                raise Exception(f"Invalid session for account {self.account_id}")
        except Exception as e:
            print(f"Error starting account {self.account_id}: {e}")
            # Обновить статус аккаунта в базе данных на неактивный
            account = self.db.get_account(self.account_id)
            if account:
                account.is_active = False
                self.db.update_account(account)
            raise e

    async def check_session_validity(self) -> bool:
        """Проверить действительность сессии"""
        try:
            if self.listener.client.is_connected():
                me = await self.listener.client.get_me()
                return me is not None
        except Exception:
            pass
        return False

    async def stop(self):
        """Остановить аккаунт"""
        await self.listener.stop()
        print(f"Account {self.account_id} stopped")

    def _handle_message(self, context: MessageContext):
        """Обработчик новых сообщений (вызывается синхронно)"""
        # Запустить асинхронную обработку
        asyncio.create_task(self._process_message(context))

    async def _process_message(self, context: MessageContext):
        """Обработать сообщение"""
        self.stats["messages_received"] += 1
        self.stats["last_activity"] = datetime.now()
        
        # Сохранить в память
        self.memory_manager.save_message(context)
        
        # Получить контекст
        chat_history = self.memory_manager.get_chat_history(context.chat_id, limit=20)
        user_profile = self.memory_manager.get_user_profile(context.user_id, context.username)
        
        # Принять решение
        decision = self.decision_engine.make_decision(
            context=context,
            chat_history_count=len(chat_history),
            user_profile=user_profile,
            recent_responses_count=self._get_recent_responses_count(context.chat_id),
        )
        
        # Обработать решение
        if decision.decision_type == DecisionType.RESPOND:
            await self._respond_to_message(context, decision, chat_history, user_profile)
        elif decision.decision_type == DecisionType.REACT:
            # Реакции пока не реализованы
            self.memory_manager.log_interaction(
                context.chat_id,
                "react",
                context.message_id,
                importance_score=decision.importance_score,
                decision_reason=decision.reason,
            )
        else:
            # Игнорировать или отложить
            self.memory_manager.log_interaction(
                context.chat_id,
                "ignore",
                context.message_id,
                importance_score=decision.importance_score,
                decision_reason=decision.reason,
            )
            self.stats["messages_ignored"] += 1
            
            # Эволюция на основе игнорирования
            if decision.decision_type == DecisionType.IGNORE:
                self.personality_engine.evolve_from_interaction(
                    "ignored",
                    {"user_id": context.user_id, "topic_keywords": context.topic_keywords},
                )

    async def _respond_to_message(
        self,
        context: MessageContext,
        decision: "Decision",
        chat_history: list,
        user_profile,
    ):
        """Ответить на сообщение"""
        # Задержка перед ответом
        if decision.delay:
            await asyncio.sleep(decision.delay)
        
        # Построить контекст для LLM
        llm_context = self.memory_manager.build_context_for_llm(context.chat_id, limit=20)
        user_context = self.memory_manager.get_user_context(context.user_id)
        topic_context = self.memory_manager.get_topic_context(context.topic_keywords)
        
        # Построить промпт
        prompt = self.prompt_builder.build_prompt(
            context,
            llm_context["chat_history"],
            user_context,
            topic_context,
        )
        
        # Сгенерировать ответ
        response_text = self.llm_service.generate_response(prompt, max_tokens=200)
        
        # Применить стиль личности (упрощенная версия)
        response_text = self._apply_personality_style(response_text)
        
        # Отправить сообщение
        try:
            message_id = await self.listener.send_message(int(context.chat_id), response_text)
            
            # Обновить статистику
            self.stats["messages_responded"] += 1
            
            # Обновить память
            self.memory_manager.update_user_interaction(
                context.user_id,
                context,
                response_sent=True,
            )
            
            # Обновить память о темах
            for keyword in context.topic_keywords:
                self.memory_manager.update_topic_discussion(keyword)
            
            # Записать в лог
            self.memory_manager.log_interaction(
                context.chat_id,
                "message",
                message_id,
                response_text=response_text,
                importance_score=decision.importance_score,
                decision_reason=decision.reason,
            )
            
            # Эволюция личности
            self.personality_engine.evolve_from_interaction(
                "responded",
                {
                    "user_id": context.user_id,
                    "topic_keywords": context.topic_keywords,
                    "tone": context.tone,
                },
            )
            
        except Exception as e:
            print(f"Error sending message: {e}")

    def _apply_personality_style(self, text: str) -> str:
        """Применить стиль личности к тексту (упрощенная версия)"""
        # В реальной системе это должно быть более сложно
        # Здесь просто пример
        
        base = self.profile.base
        
        # Применение длины сообщения
        if base.message_length == "короткий":
            # Обрезать до 1-2 предложений
            sentences = text.split(". ")
            if len(sentences) > 2:
                text = ". ".join(sentences[:2]) + "."
        
        # Применение эмодзи
        if base.emoji_usage == "никогда":
            # Удалить эмодзи (упрощенно)
            import re
            text = re.sub(r'[^\w\s\.,!?;:()\-]', '', text)
        elif base.emoji_usage == "часто":
            # Добавить эмодзи (упрощенно, в реальности нужен более умный подход)
            pass  # Пока не реализовано
        
        return text

    def _get_recent_responses_count(self, chat_id: str, minutes: int = 60) -> int:
        """Получить количество недавних ответов"""
        return self.memory_manager.get_recent_messages_count(chat_id, minutes)

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику аккаунта"""
        # Получить актуальный статус аккаунта из базы данных
        account = self.db.get_account(self.account_id)
        return {
            "id": self.account_id,
            "phone_number": account.phone_number if account else "N/A",
            "is_active": account.is_active if account else False,
            **self.stats,
            "profile": self.profile.to_dict(),
        }

