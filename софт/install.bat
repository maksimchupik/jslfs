@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 Установка зависимостей для Telegram Accounts Control
echo ============================================================
echo.

cd /d "%~dp0"

echo 🐍 Проверка Python...
python --version
if errorlevel 1 (
    echo ❌ Python не найден!
    echo Установите Python с https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 📦 Обновление pip...
python -m pip install --upgrade pip

echo.
echo 📋 Установка зависимостей из requirements.txt...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ⚠️  Произошли ошибки при установке
    echo Попробуйте запустить: python install_dependencies.py
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✅ Установка завершена!
echo ============================================================
echo.
echo 📝 Следующие шаги:
echo 1. Создайте файл .env (см. INSTALLATION_GUIDE.md)
echo 2. Запустите: python main.py
echo 3. Откройте: http://localhost:8000
echo.
pause

