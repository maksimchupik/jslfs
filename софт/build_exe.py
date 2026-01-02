"""
Скрипт для сборки exe файла из Python приложения
Использует PyInstaller
"""

import PyInstaller.__main__
import shutil
from pathlib import Path

def build_exe():
    """Собрать exe файл"""
    
    print("🔨 Начало сборки exe файла...")
    print("=" * 60)
    
    # Очистить предыдущие сборки
    dist_dir = Path("dist")
    build_dir = Path("build")
    spec_file = Path("telegram_accounts.spec")
    
    if dist_dir.exists():
        print("🧹 Очистка предыдущих сборок...")
        shutil.rmtree(dist_dir)
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Параметры для PyInstaller
    args = [
        "main.py",  # Главный файл
        "--name=TelegramAccountsControl",  # Имя exe файла
        "--onefile",  # Один exe файл
        "--windowed",  # Без консоли (закомментируйте, если нужна консоль)
        "--icon=NONE",  # Иконка (если есть, укажите путь)
        "--add-data=web;web",  # Включить веб-интерфейс
        "--add-data=user_accounts_system;user_accounts_system",  # Включить модули
        "--hidden-import=uvicorn.lifespan.on",  # Скрытые импорты
        "--hidden-import=uvicorn.lifespan.off",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.http.h11_impl",
        "--hidden-import=uvicorn.protocols.http.httptools_impl",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.protocols.websockets.websockets_impl",
        "--hidden-import=uvicorn.protocols.websockets.wsproto_impl",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.loops.asyncio",
        "--hidden-import=uvicorn.loops.uvloop",
        "--hidden-import=telethon",
        "--hidden-import=telethon.sessions",
        "--hidden-import=telethon.tl",
        "--hidden-import=fastapi",
        "--hidden-import=fastapi.staticfiles",
        "--hidden-import=fastapi.middleware.cors",
        "--hidden-import=openai",
        "--collect-all=telethon",  # Собрать все подмодули telethon
        "--collect-all=fastapi",  # Собрать все подмодули fastapi
        "--collect-all=uvicorn",  # Собрать все подмодули uvicorn
    ]
    
    # Если нужна консоль для отладки, раскомментируйте следующую строку
    # и закомментируйте --windowed выше
    # args.remove("--windowed")
    
    print("📦 Запуск PyInstaller...")
    PyInstaller.__main__.run(args)
    
    print("\n" + "=" * 60)
    print("✅ Сборка завершена!")
    print(f"📁 Exe файл находится в папке: {dist_dir.absolute()}")
    print("\n⚠️  ВАЖНО:")
    print("1. Создайте файл .env в той же папке, где находится exe")
    print("2. Скопируйте папку 'web' рядом с exe файлом (если не включена)")
    print("3. См. INSTALLATION_GUIDE.md для подробной инструкции")
    print("=" * 60)


if __name__ == "__main__":
    try:
        build_exe()
    except Exception as e:
        print(f"\n❌ Ошибка при сборке: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

