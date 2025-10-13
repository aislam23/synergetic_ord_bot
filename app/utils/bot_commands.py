"""
Управление командами бота
"""
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from loguru import logger

from app.config import settings


# Команды для обычных пользователей
USER_COMMANDS = [
    BotCommand(command="start", description="🚀 Запуск бота"),
    BotCommand(command="menu", description="📋 Главное меню"),
    BotCommand(command="help", description="❓ Помощь"),
    BotCommand(command="status", description="📊 Статус бота"),
    BotCommand(command="cancel", description="❌ Отменить текущее действие"),
]

# Дополнительные команды для админов
ADMIN_COMMANDS = [
    BotCommand(command="start", description="🚀 Запуск бота"),
    BotCommand(command="menu", description="📋 Главное меню"),
    BotCommand(command="admin", description="👑 Админ-панель"),
    BotCommand(command="help", description="❓ Помощь"),
    BotCommand(command="status", description="📊 Статус бота"),
    BotCommand(command="cancel", description="❌ Отменить текущее действие"),
]


async def setup_bot_commands(bot: Bot) -> None:
    """
    Настройка команд бота с разными областями видимости
    
    Args:
        bot: Экземпляр бота
    """
    try:
        # Устанавливаем команды по умолчанию для всех пользователей
        await bot.set_my_commands(
            commands=USER_COMMANDS,
            scope=BotCommandScopeDefault()
        )
        logger.info("✅ User commands set successfully")
        
        # Устанавливаем команды для админов
        for admin_id in settings.admin_user_ids:
            try:
                await bot.set_my_commands(
                    commands=ADMIN_COMMANDS,
                    scope=BotCommandScopeChat(chat_id=admin_id)
                )
                logger.info(f"✅ Admin commands set for user {admin_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to set admin commands for user {admin_id}: {e}")
        
        logger.info("✅ All bot commands configured successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to setup bot commands: {e}")
        raise


async def update_admin_commands(bot: Bot, admin_id: int, is_admin: bool = True) -> None:
    """
    Обновить команды для конкретного пользователя
    
    Args:
        bot: Экземпляр бота
        admin_id: ID пользователя
        is_admin: True - установить админские команды, False - обычные
    """
    try:
        commands = ADMIN_COMMANDS if is_admin else USER_COMMANDS
        await bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeChat(chat_id=admin_id)
        )
        logger.info(f"✅ Commands updated for user {admin_id} (admin={is_admin})")
    except Exception as e:
        logger.error(f"❌ Failed to update commands for user {admin_id}: {e}")
        raise


async def remove_user_commands(bot: Bot, user_id: int) -> None:
    """
    Удалить пользовательские команды (вернуть к стандартным)
    
    Args:
        bot: Экземпляр бота
        user_id: ID пользователя
    """
    try:
        await bot.delete_my_commands(
            scope=BotCommandScopeChat(chat_id=user_id)
        )
        logger.info(f"✅ User commands removed for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to remove commands for user {user_id}: {e}")
        raise

