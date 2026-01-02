"""
Пример создания сессии для Telegram аккаунта
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Получить с https://my.telegram.org/apps
API_ID = 30490628  # Ваш API ID
API_HASH = "784f0e6b8753baca72272844f09d3b05"  # Ваш API Hash


async def create_session():
    """Создать сессию для аккаунта"""
    
    # Создать клиент
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    await client.start()
    
    # Получить строку сессии
    session_string = client.session.save()
    
    print("=" * 50)
    print("SESSION STRING (сохраните это!):")
    print(session_string)
    print("=" * 50)
    
    # Получить информацию об аккаунте
    me = await client.get_me()
    print(f"Account: {me.first_name} {me.last_name or ''}")
    print(f"Username: @{me.username}" if me.username else "No username")
    print(f"Phone: {me.phone}")
    
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(create_session())

