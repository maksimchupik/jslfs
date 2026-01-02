"""
Главный orchestrator для управления всеми аккаунтами
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from .database.db_manager import DatabaseManager
from .database.models import Account
from .account_manager import AccountManager
from .llm.llm_service import LLMService


class Orchestrator:
    """Главный orchestrator системы"""

    def __init__(
        self,
        db_path: str = "data/accounts.db",
        llm_provider: str = "openai",
        llm_api_key: Optional[str] = None,
        llm_model: str = "gpt-4o-mini",
    ):
        """
        Args:
            db_path: Путь к БД
            llm_provider: Провайдер LLM
            llm_api_key: API ключ для LLM
            llm_model: Модель LLM
        """
        self.db = DatabaseManager(db_path)
        self.llm_service = LLMService(
            provider=llm_provider,
            api_key=llm_api_key,
            model=llm_model,
        )
        self.account_managers: Dict[int, AccountManager] = {}
        self.is_running = False

    def register_account(
        self,
        phone_number: str,
        session_string: str,
        api_id: int,
        api_hash: str,
    ) -> int:
        """
        Зарегистрировать новый аккаунт
        
        Args:
            phone_number: Номер телефона
            session_string: Сессия в формате StringSession
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            
        Returns:
            ID аккаунта
        """
        # Создать аккаунт в БД
        account = Account(
            phone_number=phone_number,
            session_file=f"sessions/{phone_number}.session",
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
        )
        account_id = self.db.create_account(account)
        
        # Создать менеджер аккаунта
        manager = AccountManager(
            account_id=account_id,
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
            db_manager=self.db,
            llm_service=self.llm_service,
        )
        
        self.account_managers[account_id] = manager
        
        return account_id

    async def start_account(self, account_id: int):
        """Запустить аккаунт"""
        if account_id not in self.account_managers:
            # Загрузить из БД
            account = self.db.get_account(account_id)
            if not account:
                raise ValueError(f"Account {account_id} not found")

            # Для полноценной реализации нужно хранить api_id, api_hash, session_string в БД
            # или использовать другой подход для их хранения
            # Пока что мы не можем запустить аккаунт, если эти данные не доступны

            # Временное решение - добавим метод для регистрации аккаунта с полной информацией
            raise ValueError(f"Account {account_id} needs to be registered with full credentials before starting. Use register_account method first.")
        else:
            manager = self.account_managers[account_id]
            await manager.start()

    async def stop_account(self, account_id: int):
        """Остановить аккаунт"""
        if account_id in self.account_managers:
            await self.account_managers[account_id].stop()

    async def start_all(self):
        """Запустить все активные аккаунты"""
        accounts = self.db.get_all_accounts()
        
        for account in accounts:
            if account.is_active:
                try:
                    await self.start_account(account.id)
                except Exception as e:
                    print(f"Error starting account {account.id}: {e}")
        
        self.is_running = True

    async def stop_all(self):
        """Остановить все аккаунты"""
        for account_id in list(self.account_managers.keys()):
            await self.stop_account(account_id)
        
        self.is_running = False

    def get_account_stats(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Получить статистику аккаунта"""
        if account_id in self.account_managers:
            return self.account_managers[account_id].get_stats()
        else:
            # Если аккаунт не запущен, возвращаем базовую информацию из БД
            account = self.db.get_account(account_id)
            if account:
                # Возвращаем минимальную информацию об аккаунте
                profile = self.db.get_personality_profile(account_id)
                if profile:
                    return {
                        "id": account.id,
                        "phone_number": account.phone_number,
                        "is_active": account.is_active,
                        "profile": profile.to_dict(),
                        "stats": {
                            "messages_received": 0,
                            "messages_responded": 0,
                            "messages_ignored": 0,
                            "last_activity": None,
                        }
                    }
                else:
                    return {
                        "id": account.id,
                        "phone_number": account.phone_number,
                        "is_active": account.is_active,
                        "profile": None,
                        "stats": None
                    }
        return None

    def get_all_accounts_info(self) -> List[Dict[str, Any]]:
        """Получить информацию о всех аккаунтах"""
        accounts = self.db.get_all_accounts()
        return [
            {
                "id": acc.id,
                "phone_number": acc.phone_number,
                "is_active": acc.is_active,
                "stats": self.get_account_stats(acc.id),
            }
            for acc in accounts
        ]

    async def check_account_sessions(self) -> Dict[int, bool]:
        """Проверить действительность сессий всех аккаунтов"""
        results = {}

        # Получить все аккаунты из базы данных
        all_accounts = self.db.get_all_accounts()

        for account in all_accounts:
            # Если аккаунт запущен, используем его менеджер
            if account.id in self.account_managers:
                manager = self.account_managers[account.id]
                is_valid = await manager.check_session_validity()
            else:
                # Если аккаунт не запущен, создаем временный клиент для проверки сессии
                is_valid = await self._check_session_validity_standalone(account.id)

            results[account.id] = is_valid

            # Обновить статус аккаунта в базе данных
            account.is_active = is_valid
            self.db.update_account(account)

        return results

    async def _check_session_validity_standalone(self, account_id: int) -> bool:
        """Проверить действительность сессии для незапущенного аккаунта"""
        from .listener.message_listener import MessageListener
        from telethon import TelegramClient
        from telethon.sessions import StringSession

        # Получить информацию об аккаунте из базы данных
        account = self.db.get_account(account_id)
        if not account or not account.session_string or not account.api_id or not account.api_hash:
            return False

        # Создать временный клиент для проверки сессии
        try:
            client = TelegramClient(
                StringSession(account.session_string),
                account.api_id,
                account.api_hash
            )

            # Подключиться и проверить сессию
            await client.connect()

            # Попробовать получить информацию об аккаунте
            me = await client.get_me()
            is_valid = me is not None

            await client.disconnect()

            return is_valid
        except Exception as e:
            print(f"Error checking session validity for account {account_id}: {e}")
            return False

