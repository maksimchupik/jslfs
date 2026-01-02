"""
Пример базового использования системы
"""

import asyncio
import os
from dotenv import load_dotenv

from user_accounts_system.orchestrator import Orchestrator
from user_accounts_system.api.control_api import create_app
import uvicorn

# Загрузить переменные окружения
load_dotenv()


async def main():
    """Основная функция"""
    
    # Инициализация orchestrator
    orchestrator = Orchestrator(
        db_path="data/accounts.db",
        llm_provider="openai",
        llm_api_key=os.getenv("OPENAI_API_KEY"),
        llm_model="gpt-4o-mini",
    )
    
    # Регистрация аккаунта
    # ВАЖНО: session_string должен быть получен заранее через Telethon
    account_id = orchestrator.register_account(
        phone_number="+1234567890",
        session_string=os.getenv("TELEGRAM_SESSION_STRING"),  # StringSession
        api_id=int(os.getenv("TELEGRAM_API_ID")),
        api_hash=os.getenv("TELEGRAM_API_HASH"),
    )
    
    print(f"Account registered with ID: {account_id}")
    
    # Запуск аккаунта
    await orchestrator.start_account(account_id)
    
    # Запуск API сервера (в отдельном потоке)
    app = create_app(orchestrator)
    
    # Запустить API сервер
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    
    # Запустить в фоне
    await asyncio.gather(
        server.serve(),
        asyncio.sleep(3600),  # Работать 1 час
    )
    
    # Остановка
    await orchestrator.stop_all()


if __name__ == "__main__":
    asyncio.run(main())

