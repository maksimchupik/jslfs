"""
Главный файл приложения для запуска системы управления Telegram аккаунтами
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from user_accounts_system.orchestrator import Orchestrator
from user_accounts_system.api.control_api import create_app
import uvicorn

# Загрузить переменные окружения
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print("Внимание: Файл .env не найден!")
    print("Создайте файл .env в папке с программой.")
    print("См. инструкцию в INSTALLATION_GUIDE.md")
    input("\nНажмите Enter для продолжения (программа может работать некорректно)...")


def get_resource_path(relative_path):
    """Получить путь к ресурсам (работает и в exe, и в обычном режиме)"""
    if getattr(sys, 'frozen', False):
        # Если запущено как exe
        base_path = Path(sys._MEIPASS)
    else:
        # Если запущено как скрипт
        base_path = Path(__file__).parent
    return base_path / relative_path


def ensure_web_directory():
    """Убедиться, что папка web доступна (для exe)"""
    if getattr(sys, 'frozen', False):
        # В exe режиме копируем web из временной папки
        import shutil
        exe_dir = Path(sys.executable).parent
        web_dir = exe_dir / "web"
        if not web_dir.exists():
            temp_web = Path(sys._MEIPASS) / "web"
            if temp_web.exists():
                shutil.copytree(temp_web, web_dir)
                print(f"📁 Папка web скопирована в {web_dir}")
        return web_dir
    else:
        return Path(__file__).parent / "web"


async def main():
    """Основная функция"""
    
    print("=" * 60)
    print("Запуск системы управления Telegram аккаунтами")
    print("=" * 60)
    
    # Создать папку для данных, если её нет
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Инициализация orchestrator
    print("\nИнициализация системы...")
    orchestrator = Orchestrator(
        db_path=str(data_dir / "accounts.db"),
        llm_provider="openai",
        llm_api_key=os.getenv("OPENAI_API_KEY"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )

    # Проверка наличия API ключа
    if not os.getenv("OPENAI_API_KEY"):
        print("\nВНИМАНИЕ: OPENAI_API_KEY не установлен в .env файле!")
        print("Система будет работать, но LLM функции будут недоступны.")

    # Загрузка существующих аккаунтов из БД
    accounts = orchestrator.db.get_all_accounts()
    if accounts:
        print(f"\nНайдено аккаунтов в базе: {len(accounts)}")
        for acc in accounts:
            print(f"   - ID: {acc.id}, Телефон: {acc.phone_number}, Активен: {acc.is_active}")

    # Запуск API сервера
    print("\nЗапуск веб-интерфейса...")
    app = create_app(orchestrator)

    # Получить порт из переменной окружения или использовать 8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"\nСистема запущена!")
    print(f"Веб-интерфейс доступен по адресу: http://localhost:{port}")
    print(f"API доступен по адресу: http://localhost:{port}/docs")
    print("\nИспользуйте веб-интерфейс для управления аккаунтами")
    print("   или REST API для программного управления.")
    print("\nДля остановки нажмите Ctrl+C")
    print("=" * 60)
    
    # Запустить API сервер
    config = uvicorn.Config(
        app, 
        host=host, 
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\n\n🛑 Остановка системы...")
        await orchestrator.stop_all()
        print("✅ Система остановлена")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nДо свидания!")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

