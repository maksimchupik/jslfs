"""
Listener для прослушивания сообщений через MTProto
"""

import asyncio
from typing import Callable, Optional, Dict, Any
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from .message_parser import MessageParser, MessageContext


class MessageListener:
    """Listener для прослушивания новых сообщений через MTProto"""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_string: str,
        account_username: Optional[str] = None,
    ):
        """
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_string: Сессия в формате StringSession
            account_username: Username аккаунта для определения упоминаний
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.account_username = account_username
        
        self.client: Optional[TelegramClient] = None
        self.parser = MessageParser(account_username)
        self.message_handler: Optional[Callable[[MessageContext], None]] = None
        self.is_running = False

    async def start(self):
        """Запустить listener"""
        if self.is_running:
            return

        # Создать клиент из строки сессии
        session = StringSession(self.session_string)
        self.client = TelegramClient(session, self.api_id, self.api_hash)

        # Подключиться к Telegram
        await self.client.connect()

        # Убедиться, что сессия действительна
        if not await self.client.is_user_authorized():
            print(f"Session is not authorized for account {self.account_username}")
            raise Exception("Session is not valid. Please create a new session string.")

        self.is_running = True

        # Подписаться на новые сообщения
        @self.client.on(events.NewMessage)
        async def handler(event):
            await self._handle_message(event)

        print(f"MessageListener started for account {self.account_username}")

    async def stop(self):
        """Остановить listener"""
        if self.client:
            await self.client.disconnect()
            self.client = None
        self.is_running = False

    def set_message_handler(self, handler: Callable[[MessageContext], None]):
        """Установить обработчик новых сообщений"""
        self.message_handler = handler

    async def _handle_message(self, event: events.NewMessage.Event):
        """Обработать новое сообщение"""
        if not self.message_handler:
            return

        # Преобразовать событие в словарь
        message_data = {
            "id": event.message.id,
            "chat_id": event.chat_id,
            "text": event.message.text,
            "message": event.message.text,
            "from_id": {
                "user_id": event.sender_id,
                "username": getattr(event.sender, "username", None),
            },
            "reply_to": None,
        }

        # Обработка reply
        if event.message.reply_to:
            reply_to = await event.get_reply_message()
            if reply_to:
                message_data["reply_to"] = {
                    "reply_to_msg_id": reply_to.id,
                    "from_id": {
                        "user_id": reply_to.sender_id,
                    },
                }

        # Парсинг контекста
        context = self.parser.parse(message_data)

        # Вызов обработчика
        if self.message_handler:
            self.message_handler(context)

    async def send_message(self, chat_id: int, text: str) -> Optional[int]:
        """Отправить сообщение"""
        if not self.client:
            return None
        
        try:
            message = await self.client.send_message(chat_id, text)
            return message.id
        except Exception as e:
            print(f"Error sending message: {e}")
            return None

    async def edit_profile(self, first_name: Optional[str] = None, 
                          last_name: Optional[str] = None,
                          bio: Optional[str] = None):
        """Изменить профиль аккаунта"""
        if not self.client:
            return
        
        try:
            await self.client.edit_profile(
                first_name=first_name,
                last_name=last_name,
                about=bio
            )
        except Exception as e:
            print(f"Error editing profile: {e}")

    async def set_profile_photo(self, photo_path: str):
        """Установить фото профиля"""
        if not self.client:
            return
        
        try:
            await self.client.upload_profile_photo(photo_path)
        except Exception as e:
            print(f"Error setting profile photo: {e}")

