"""
Middleware для работы с пользователями
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User, Message
from loguru import logger

from app.database import db
from app.config import settings


class UserMiddleware(BaseMiddleware):
    """Middleware для проверки доступа пользователей"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем пользователя из события
        user: User = data.get("event_from_user")
        
        if user and not user.is_bot:
            # Проверяем, является ли это командой /start (разрешаем всегда)
            if isinstance(event, Message) and event.text and event.text.startswith('/start'):
                return await handler(event, data)
            
            try:
                # Получаем пользователя из базы данных
                db_user = await db.get_user(user.id)
                
                # Проверяем доступ
                # 1. Если пользователь не в базе и не админ из конфига - блокируем
                if not db_user and not settings.is_admin(user.id):
                    if isinstance(event, Message):
                        await event.answer(
                            "❌ <b>Доступ запрещен</b>\n\n"
                            "Для использования бота необходима пригласительная ссылка от администратора.\n\n"
                            "Обратитесь к администратору вашей компании для получения доступа."
                        )
                    return
                
                # 2. Если пользователь заблокирован - блокируем
                if db_user and db_user.is_blocked:
                    if isinstance(event, Message):
                        await event.answer(
                            "🚫 <b>Доступ заблокирован</b>\n\n"
                            "Ваш доступ к боту был заблокирован администратором.\n\n"
                            "Для получения дополнительной информации обратитесь к администратору."
                        )
                    return
                
                # 3. Если пользователь админ из конфига, но не в базе - добавляем
                if not db_user and settings.is_admin(user.id):
                    await db.add_user_with_invite(
                        user_id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        role="admin"
                    )
                
                # Добавляем информацию о пользователе в data для использования в хендлерах
                if db_user:
                    data["db_user"] = db_user
                
            except Exception as e:
                logger.error(f"Ошибка при проверке доступа пользователя {user.id}: {e}")
        
        # Продолжаем обработку
        return await handler(event, data) 