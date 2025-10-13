"""
Обработчик команды /start
"""
from datetime import datetime
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject

from app.database import db
from app.keyboards.creative import get_main_menu_keyboard
from app.config import settings
from app.utils.bot_commands import update_admin_commands

router = Router()


@router.message(CommandStart(deep_link=True))
async def start_with_invite_link(message: Message, command: CommandObject, bot: Bot):
    """Обработчик команды /start с пригласительной ссылкой"""
    user = message.from_user
    invite_code = command.args
    
    # Проверяем пригласительную ссылку
    invite_link = await db.get_invite_link_by_code(invite_code)
    
    if not invite_link:
        await message.answer(
            "❌ <b>Неверная пригласительная ссылка</b>\n\n"
            "Эта ссылка не существует или была удалена."
        )
        return
    
    if invite_link.is_used:
        await message.answer(
            "❌ <b>Ссылка уже использована</b>\n\n"
            "Эта пригласительная ссылка уже была использована и больше не действительна.\n"
            "Обратитесь к администратору для получения новой ссылки."
        )
        return
    
    # Проверяем срок действия
    if invite_link.expires_at and invite_link.expires_at < datetime.utcnow():
        await message.answer(
            "❌ <b>Ссылка просрочена</b>\n\n"
            "Срок действия этой пригласительной ссылки истек.\n"
            "Обратитесь к администратору для получения новой ссылки."
        )
        return
    
    # Используем ссылку и регистрируем пользователя
    await db.use_invite_link(invite_code, user.id)
    
    # Добавляем пользователя с указанной ролью
    await db.add_user_with_invite(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=invite_link.full_name,
        role=invite_link.target_role,
        invited_by=invite_link.created_by
    )
    
    # Обновляем команды бота для нового пользователя
    try:
        is_admin = invite_link.target_role == "admin"
        await update_admin_commands(bot, user.id, is_admin)
    except Exception as e:
        # Не критично, если не удалось обновить команды
        pass
    
    # Приветственное сообщение
    role_text = "администратора" if invite_link.target_role == "admin" else "сотрудника"
    
    welcome_text = f"""
✅ <b>Успешная регистрация!</b>

👋 Привет, {invite_link.full_name or user.first_name or 'пользователь'}!

Вы зарегистрированы в боте как <b>{role_text}</b>.

<b>Добро пожаловать в бот для создания токенов Erid!</b>

Этот бот поможет вам создать креативы саморекламы и получить токены Erid через сервис Медиаскаут.

🎨 <b>Что можно сделать:</b>
• Создать креатив для саморекламы
• Выбрать форму креатива (баннер, текст, видео и т.д.)
• Загрузить медиа-файлы
• Получить токен Erid

Для начала работы используйте команду /menu или выберите действие ниже:
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(CommandStart())
async def start_command(message: Message, bot: Bot):
    """Обработчик команды /start без параметров"""
    user = message.from_user
    
    # Проверяем, есть ли пользователь в базе
    existing_user = await db.get_user(user.id)
    
    # Если пользователь не зарегистрирован и не является админом из конфига
    if not existing_user and not settings.is_admin(user.id):
        await message.answer(
            "❌ <b>Доступ запрещен</b>\n\n"
            "Для использования бота необходима пригласительная ссылка от администратора.\n\n"
            "Обратитесь к администратору вашей компании для получения доступа."
        )
        return
    
    # Если пользователь админ из конфига, но не в базе - добавляем его
    if not existing_user and settings.is_admin(user.id):
        await db.add_user_with_invite(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            role="admin"
        )
        existing_user = await db.get_user(user.id)
        
        # Обновляем команды для админа
        try:
            await update_admin_commands(bot, user.id, is_admin=True)
        except Exception as e:
            # Не критично, если не удалось обновить команды
            pass
    
    # Проверяем, не заблокирован ли пользователь
    if existing_user and existing_user.is_blocked:
        await message.answer(
            "🚫 <b>Доступ заблокирован</b>\n\n"
            "Ваш доступ к боту был заблокирован администратором.\n\n"
            "Для получения дополнительной информации обратитесь к администратору."
        )
        return
    
    # Приветственное сообщение
    welcome_text = f"""
👋 Привет, {user.first_name or 'пользователь'}!

<b>Добро пожаловать в бот для создания токенов Erid!</b>

Этот бот поможет вам создать креативы саморекламы и получить токены Erid через сервис Медиаскаут.

🎨 <b>Что можно сделать:</b>
• Создать креатив для саморекламы
• Выбрать форму креатива (баннер, текст, видео и т.д.)
• Загрузить медиа-файлы
• Получить токен Erid

Для начала работы используйте команду /menu или выберите действие ниже:
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )
