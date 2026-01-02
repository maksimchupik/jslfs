"""
Скрипт для автоматической установки всех зависимостей
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Выполнить команду и показать результат"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        print(result.stdout)
        if result.stderr:
            print("Предупреждения:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        print(f"Вывод: {e.stdout}")
        print(f"Ошибки: {e.stderr}")
        return False

def check_python():
    """Проверить наличие Python"""
    print("\n🐍 Проверка Python...")
    try:
        version = sys.version
        print(f"✅ Python найден: {version.split()[0]}")
        return True
    except Exception as e:
        print(f"❌ Python не найден: {e}")
        print("\n⚠️  Установите Python с https://www.python.org/downloads/")
        return False

def check_pip():
    """Проверить наличие pip"""
    print("\n📦 Проверка pip...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            print(f"✅ pip найден: {result.stdout.strip()}")
            return True
        else:
            print("❌ pip не найден, пытаюсь установить...")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки pip: {e}")
        return False

def upgrade_pip():
    """Обновить pip до последней версии"""
    print("\n⬆️  Обновление pip...")
    return run_command(
        f'"{sys.executable}" -m pip install --upgrade pip',
        "Обновление pip"
    )

def install_requirements():
    """Установить зависимости из requirements.txt"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"❌ Файл requirements.txt не найден в {requirements_file.parent}")
        return False
    
    print(f"\n📋 Установка зависимостей из {requirements_file}")
    
    # Читаем файл requirements.txt
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"Найдено зависимостей: {len(requirements)}")
    
    # Устанавливаем каждую зависимость отдельно для лучшего контроля
    failed = []
    for i, req in enumerate(requirements, 1):
        print(f"\n[{i}/{len(requirements)}] Установка: {req}")
        success = run_command(
            f'"{sys.executable}" -m pip install "{req}"',
            f"Установка {req}"
        )
        if not success:
            failed.append(req)
            print(f"⚠️  Не удалось установить {req}, продолжаю...")
    
    if failed:
        print(f"\n⚠️  Не удалось установить {len(failed)} зависимостей:")
        for req in failed:
            print(f"   - {req}")
        return False
    
    return True

def verify_installation():
    """Проверить установку основных модулей"""
    print("\n🔍 Проверка установки...")
    
    modules_to_check = [
        ("telethon", "Telethon"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("openai", "OpenAI"),
        ("pydantic", "Pydantic"),
        ("dotenv", "python-dotenv"),
    ]
    
    all_ok = True
    for module, name in modules_to_check:
        try:
            __import__(module)
            print(f"✅ {name} установлен")
        except ImportError:
            print(f"❌ {name} НЕ установлен")
            all_ok = False
    
    return all_ok

def main():
    """Главная функция"""
    print("="*60)
    print("🚀 Установка зависимостей для Telegram Accounts Control")
    print("="*60)
    
    # Проверка Python
    if not check_python():
        input("\nНажмите Enter для выхода...")
        return
    
    # Проверка pip
    if not check_pip():
        print("\n⚠️  pip не найден. Попробуйте переустановить Python с галочкой 'Add Python to PATH'")
        input("\nНажмите Enter для выхода...")
        return
    
    # Обновление pip
    upgrade_pip()
    
    # Установка зависимостей
    if not install_requirements():
        print("\n⚠️  Некоторые зависимости не установились. Проверьте ошибки выше.")
        input("\nНажмите Enter для продолжения...")
    
    # Проверка установки
    if verify_installation():
        print("\n" + "="*60)
        print("✅ Все зависимости успешно установлены!")
        print("="*60)
        print("\n📝 Следующие шаги:")
        print("1. Создайте файл .env (см. INSTALLATION_GUIDE.md)")
        print("2. Запустите: python main.py")
        print("3. Откройте: http://localhost:8000")
    else:
        print("\n" + "="*60)
        print("⚠️  Некоторые модули не установлены")
        print("Попробуйте установить их вручную:")
        print("   pip install -r requirements.txt")
        print("="*60)
    
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Установка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

