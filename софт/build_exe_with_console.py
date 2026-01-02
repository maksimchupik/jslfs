"""
Скрипт для сборки exe файла С КОНСОЛЬЮ (для отладки)
"""

import PyInstaller.__main__
import shutil
from pathlib import Path

def build_exe():
    """Собрать exe файл с консолью"""
    
    print("🔨 Начало сборки exe файла (с консолью для отладки)...")
    print("=" * 60)
    
    # Очистить предыдущие сборки
    dist_dir = Path("dist")
    build_dir = Path("build")
    
    if dist_dir.exists():
        print("🧹 Очистка предыдущих сборок...")
        shutil.rmtree(dist_dir)
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Параметры для PyInstaller (БЕЗ --windowed, чтобы была консоль)
    args = [
        "main.py",
        "--name=TelegramAccountsControl",
        "--onefile",
        # НЕТ --windowed, чтобы была видна консоль
        "--add-data=web;web",
        "--add-data=user_accounts_system;user_accounts_system",
        "--hidden-import=uvicorn.lifespan.on",
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
        "--collect-all=telethon",
        "--collect-all=fastapi",
        "--collect-all=uvicorn",
    ]
    
    print("📦 Запуск PyInstaller...")
    PyInstaller.__main__.run(args)
    
    print("\n" + "=" * 60)
    print("✅ Сборка завершена!")
    print(f"📁 Exe файл находится в папке: {dist_dir.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        build_exe()
    except Exception as e:
        print(f"\n❌ Ошибка при сборке: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

