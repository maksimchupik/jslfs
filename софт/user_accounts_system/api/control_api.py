"""
REST API для управления системой извне
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
from pathlib import Path

from ..orchestrator import Orchestrator


# Pydantic модели для API
class AccountCreate(BaseModel):
    phone_number: str
    session_string: str
    api_id: int
    api_hash: str


class PersonalityUpdate(BaseModel):
    base_config: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None


class AccountResponse(BaseModel):
    id: int
    phone_number: str
    is_active: bool
    stats: Optional[Dict[str, Any]] = None


def create_app(orchestrator: Orchestrator) -> FastAPI:
    """Создать FastAPI приложение"""
    app = FastAPI(title="Telegram User Accounts Control API")
    
    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Подключение статических файлов (веб-интерфейс)
    web_dir = Path(__file__).parent.parent.parent / "web"
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
        
        @app.get("/")
        async def root():
            return FileResponse(str(web_dir / "index.html"))
    else:
        @app.get("/")
        async def root():
            return {"message": "Telegram User Accounts Control API", "version": "1.0.0"}
    
    @app.get("/accounts", response_model=List[AccountResponse])
    async def get_accounts():
        """Получить список всех аккаунтов"""
        accounts_info = orchestrator.get_all_accounts_info()
        return accounts_info
    
    @app.get("/accounts/{account_id}")
    async def get_account(account_id: int):
        """Получить информацию об аккаунте"""
        stats = orchestrator.get_account_stats(account_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Account not found")
        return stats
    
    @app.post("/accounts")
    async def create_account(account: AccountCreate):
        """Создать новый аккаунт"""
        try:
            account_id = orchestrator.register_account(
                phone_number=account.phone_number,
                session_string=account.session_string,
                api_id=account.api_id,
                api_hash=account.api_hash,
            )
            return {"account_id": account_id, "message": "Account created"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/accounts/{account_id}/start")
    async def start_account(account_id: int):
        """Запустить аккаунт"""
        try:
            await orchestrator.start_account(account_id)
            return {"message": f"Account {account_id} started"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/accounts/{account_id}/stop")
    async def stop_account(account_id: int):
        """Остановить аккаунт"""
        try:
            await orchestrator.stop_account(account_id)
            return {"message": f"Account {account_id} stopped"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/accounts/{account_id}/profile")
    async def get_profile(account_id: int):
        """Получить профиль личности"""
        stats = orchestrator.get_account_stats(account_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Account not found")
        
        profile = stats.get("profile")
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return profile
    
    @app.put("/accounts/{account_id}/profile")
    async def update_profile(account_id: int, update: PersonalityUpdate):
        """Обновить профиль личности"""
        # Проверяем, существует ли аккаунт в базе данных
        account = orchestrator.db.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Если аккаунт запущен, используем его менеджер
        if account_id in orchestrator.account_managers:
            manager = orchestrator.account_managers[account_id]
            personality_engine = manager.personality_engine

            try:
                if update.base_config:
                    personality_engine.update_base_config(update.base_config)

                if update.constraints:
                    personality_engine.update_constraints(update.constraints)

                return {"message": "Profile updated", "profile": personality_engine.get_profile().to_dict()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            # Если аккаунт не запущен, обновляем напрямую в базе данных
            try:
                profile = orchestrator.db.get_personality_profile(account_id)
                if not profile:
                    # Создаем профиль по умолчанию
                    from ..database.models import BasePersonalityConfig, DynamicPersonalityConfig, PersonalityConstraints, PersonalityProfile
                    from datetime import datetime
                    base = BasePersonalityConfig()
                    dynamic = DynamicPersonalityConfig()
                    constraints = PersonalityConstraints()
                    profile = PersonalityProfile(
                        account_id=account_id,
                        base=base,
                        dynamic=dynamic,
                        constraints=constraints,
                        last_updated=datetime.now()
                    )

                # Обновляем профиль
                if update.base_config:
                    for key, value in update.base_config.items():
                        if hasattr(profile.base, key):
                            setattr(profile.base, key, value)

                if update.constraints:
                    for key, value in update.constraints.items():
                        if hasattr(profile.constraints, key):
                            setattr(profile.constraints, key, value)

                # Сохраняем в базу
                orchestrator.db.save_personality_profile(profile)

                return {"message": "Profile updated", "profile": profile.to_dict()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    @app.put("/accounts/{account_id}/allowed_chats")
    async def update_allowed_chats(account_id: int, chats: List[str] = None):
        """Обновить список разрешенных чатов"""
        # Проверяем, существует ли аккаунт в базе данных
        account = orchestrator.db.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        if chats is None:
            chats = []

        # Если аккаунт запущен, используем его менеджер
        if account_id in orchestrator.account_managers:
            manager = orchestrator.account_managers[account_id]
            personality_engine = manager.personality_engine
            try:
                profile = personality_engine.update_allowed_chats(chats)
                return {"message": "Allowed chats updated", "profile": profile.to_dict()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            # Если аккаунт не запущен, обновляем напрямую в базе данных
            try:
                profile = orchestrator.db.get_personality_profile(account_id)
                if not profile:
                    # Создаем профиль по умолчанию
                    from ..database.models import BasePersonalityConfig, DynamicPersonalityConfig, PersonalityConstraints, PersonalityProfile
                    from datetime import datetime
                    base = BasePersonalityConfig()
                    dynamic = DynamicPersonalityConfig()
                    constraints = PersonalityConstraints()
                    profile = PersonalityProfile(
                        account_id=account_id,
                        base=base,
                        dynamic=dynamic,
                        constraints=constraints,
                        last_updated=datetime.now()
                    )

                # Обновляем разрешенные чаты
                profile.constraints.allowed_chats = chats

                # Сохраняем в базу
                orchestrator.db.save_personality_profile(profile)

                return {"message": "Allowed chats updated", "profile": profile.to_dict()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/accounts/{account_id}/profile/lock")
    async def lock_personality(account_id: int):
        """Заблокировать личность от изменений"""
        # Проверяем, существует ли аккаунт в базе данных
        account = orchestrator.db.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Если аккаунт запущен, используем его менеджер
        if account_id in orchestrator.account_managers:
            manager = orchestrator.account_managers[account_id]
            personality_engine = manager.personality_engine
            profile = personality_engine.lock_personality()
        else:
            # Если аккаунт не запущен, обновляем напрямую в базе данных
            profile = orchestrator.db.get_personality_profile(account_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")

            profile.constraints.personality_locked = True
            orchestrator.db.save_personality_profile(profile)

        return {"message": "Personality locked", "profile": profile.to_dict()}

    @app.post("/accounts/{account_id}/profile/unlock")
    async def unlock_personality(account_id: int):
        """Разблокировать личность"""
        # Проверяем, существует ли аккаунт в базе данных
        account = orchestrator.db.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Если аккаунт запущен, используем его менеджер
        if account_id in orchestrator.account_managers:
            manager = orchestrator.account_managers[account_id]
            personality_engine = manager.personality_engine
            profile = personality_engine.unlock_personality()
        else:
            # Если аккаунт не запущен, обновляем напрямую в базе данных
            profile = orchestrator.db.get_personality_profile(account_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")

            profile.constraints.personality_locked = False
            orchestrator.db.save_personality_profile(profile)

        return {"message": "Personality unlocked", "profile": profile.to_dict()}
    
    @app.get("/accounts/{account_id}/memory")
    async def get_memory(account_id: int, chat_id: Optional[str] = None):
        """Получить память аккаунта"""
        if account_id not in orchestrator.account_managers:
            raise HTTPException(status_code=404, detail="Account not found")
        
        manager = orchestrator.account_managers[account_id]
        memory = manager.memory_manager
        
        if chat_id:
            history = memory.get_chat_history(chat_id, limit=50)
            return {"chat_history": [msg.to_dict() for msg in history]}
        else:
            # Вернуть общую информацию о памяти
            return {"message": "Use ?chat_id=... to get specific chat history"}
    
    @app.post("/accounts/{account_id}/memory/clear")
    async def clear_memory(account_id: int, chat_id: Optional[str] = None):
        """Очистить память (не реализовано полностью)"""
        return {"message": "Memory clearing not fully implemented"}
    
    @app.get("/accounts/{account_id}/stats")
    async def get_stats(account_id: int):
        """Получить статистику аккаунта"""
        stats = orchestrator.get_account_stats(account_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Account not found")
        return stats

    @app.post("/accounts/check_sessions")
    async def check_all_sessions():
        """Проверить действительность сессий всех аккаунтов"""
        try:
            results = await orchestrator.check_account_sessions()
            return {"message": "Session check completed", "results": results}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return app

