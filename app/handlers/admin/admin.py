"""
Админские хендлеры
"""
import re
from datetime import datetime
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.config import settings
from app.database import db
from app.states import AdminStates
from app.keyboards import AdminKeyboards
from app.services import BroadcastService

router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    return settings.is_admin(user_id)


@router.message(Command("admin"))
async def admin_command(message: Message, bot: Bot):
    """Обработчик команды /admin"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    # Получаем статистику бота
    stats = await db.get_bot_stats()
    if not stats:
        # Если статистики нет, создаем её
        stats = await db.update_bot_stats()
    
    # Получаем актуальные данные
    total_users = await db.get_users_count()
    active_users = await db.get_active_users_count()
    
    # Форматируем время последнего запуска
    last_restart = stats.last_restart.strftime("%d.%m.%Y %H:%M:%S")
    
    # Формируем сообщение со статистикой
    text = f"""
🔧 <b>Админская панель</b>

📊 <b>Статистика бота:</b>
👥 Всего пользователей: <b>{total_users}</b>
✅ Активных пользователей: <b>{active_users}</b>
🟢 Статус: <b>{stats.status}</b>
🕐 Последний запуск: <b>{last_restart}</b>

Выберите действие:
"""
    
    await message.answer(
        text=text,
        reply_markup=AdminKeyboards.main_admin_menu()
    )


@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Начало создания рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    await state.set_state(AdminStates.broadcast_message)
    
    await callback.message.edit_text(
        "📤 <b>Создание рассылки</b>\n\n"
        "Отправьте сообщение любого типа (текст, фото, видео, документ и т.д.), "
        "которое хотите разослать всем пользователям бота.\n\n"
        "Для отмены введите /cancel"
    )
    
    await callback.answer()


@router.message(StateFilter(AdminStates.broadcast_message))
async def receive_broadcast_message(message: Message, state: FSMContext):
    """Получение сообщения для рассылки"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    # Сохраняем сообщение в состояние
    await state.update_data(broadcast_message=message)
    
    # Получаем количество пользователей для рассылки
    users_count = await db.get_active_users_count()
    
    await message.answer(
        f"✅ <b>Сообщение получено!</b>\n\n"
        f"👥 Количество получателей: <b>{users_count}</b>\n\n"
        f"Хотите добавить кнопку к сообщению?",
        reply_markup=AdminKeyboards.broadcast_add_button()
    )


@router.callback_query(F.data == "broadcast_add_button", StateFilter(AdminStates.broadcast_message))
async def add_button_to_broadcast(callback: CallbackQuery, state: FSMContext):
    """Добавление кнопки к рассылке"""
    await state.set_state(AdminStates.broadcast_button)
    
    await callback.message.edit_text(
        "🔗 <b>Добавление кнопки</b>\n\n"
        "Отправьте кнопку в формате:\n"
        "<code>Текст кнопки | https://example.com</code>\n\n"
        "Пример:\n"
        "<code>Наш сайт | https://example.com</code>\n\n"
        "Для отмены введите /cancel"
    )
    
    await callback.answer()


@router.message(StateFilter(AdminStates.broadcast_button))
async def receive_broadcast_button(message: Message, state: FSMContext):
    """Получение кнопки для рассылки"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    # Парсим кнопку
    button_pattern = r"^(.+?)\s*\|\s*(https?://.+)$"
    match = re.match(button_pattern, message.text.strip())
    
    if not match:
        await message.answer(
            "❌ <b>Неверный формат кнопки!</b>\n\n"
            "Используйте формат:\n"
            "<code>Текст кнопки | https://example.com</code>\n\n"
            "Попробуйте еще раз или введите /cancel для отмены"
        )
        return
    
    button_text = match.group(1).strip()
    button_url = match.group(2).strip()
    
    # Сохраняем данные кнопки
    await state.update_data(
        button_text=button_text,
        button_url=button_url
    )
    
    # Создаем превью кнопки
    preview_keyboard = AdminKeyboards.create_custom_button(button_text, button_url)
    
    await message.answer(
        f"✅ <b>Кнопка создана!</b>\n\n"
        f"📝 Текст: <b>{button_text}</b>\n"
        f"🔗 Ссылка: <code>{button_url}</code>\n\n"
        f"Превью кнопки:",
        reply_markup=preview_keyboard
    )
    
    # Переходим к подтверждению
    data = await state.get_data()
    users_count = await db.get_active_users_count()
    
    await message.answer(
        f"📤 <b>Подтверждение рассылки</b>\n\n"
        f"👥 Получателей: <b>{users_count}</b>\n"
        f"🔗 С кнопкой: <b>Да</b>\n\n"
        f"Отправить рассылку?",
        reply_markup=AdminKeyboards.broadcast_confirm(users_count)
    )


@router.callback_query(F.data == "broadcast_no_button", StateFilter(AdminStates.broadcast_message))
async def broadcast_without_button(callback: CallbackQuery, state: FSMContext):
    """Рассылка без кнопки"""
    users_count = await db.get_active_users_count()
    
    await callback.message.edit_text(
        f"📤 <b>Подтверждение рассылки</b>\n\n"
        f"👥 Получателей: <b>{users_count}</b>\n"
        f"🔗 С кнопкой: <b>Нет</b>\n\n"
        f"Отправить рассылку?",
        reply_markup=AdminKeyboards.broadcast_confirm(users_count)
    )
    
    await callback.answer()


@router.callback_query(F.data == "broadcast_confirm_yes")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Подтверждение и запуск рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    data = await state.get_data()
    broadcast_message = data.get("broadcast_message")
    
    if not broadcast_message:
        await callback.message.edit_text("❌ Ошибка: сообщение для рассылки не найдено")
        await state.clear()
        return
    
    # Создаем кнопку если есть
    custom_keyboard = None
    if data.get("button_text") and data.get("button_url"):
        custom_keyboard = AdminKeyboards.create_custom_button(
            data["button_text"],
            data["button_url"]
        )
    
    # Начинаем рассылку
    broadcast_service = BroadcastService(bot)
    
    # Сообщение о начале рассылки
    progress_message = await callback.message.edit_text(
        "📤 <b>Рассылка запущена...</b>\n\n"
        "📊 Прогресс: <b>0%</b>\n"
        "✅ Отправлено: <b>0</b>\n"
        "❌ Ошибок: <b>0</b>\n"
        "🚫 Заблокировано: <b>0</b>"
    )
    
    # Функция для обновления прогресса
    async def update_progress(stats: dict):
        progress_percent = int((stats["sent"] + stats["failed"] + stats["blocked"]) / stats["total"] * 100)
        
        try:
            await progress_message.edit_text(
                f"📤 <b>Рассылка в процессе...</b>\n\n"
                f"📊 Прогресс: <b>{progress_percent}%</b>\n"
                f"✅ Отправлено: <b>{stats['sent']}</b>\n"
                f"❌ Ошибок: <b>{stats['failed']}</b>\n"
                f"🚫 Заблокировано: <b>{stats['blocked']}</b>"
            )
        except Exception:
            # Игнорируем ошибки обновления прогресса
            pass
    
    # Запускаем рассылку
    try:
        final_stats = await broadcast_service.send_broadcast(
            message=broadcast_message,
            custom_keyboard=custom_keyboard,
            progress_callback=update_progress
        )
        
        # Финальная статистика
        success_rate = int(final_stats["sent"] / final_stats["total"] * 100) if final_stats["total"] > 0 else 0
        
        await progress_message.edit_text(
            f"✅ <b>Рассылка завершена!</b>\n\n"
            f"📊 <b>Итоговая статистика:</b>\n"
            f"👥 Всего получателей: <b>{final_stats['total']}</b>\n"
            f"✅ Успешно доставлено: <b>{final_stats['sent']}</b>\n"
            f"❌ Ошибок доставки: <b>{final_stats['failed']}</b>\n"
            f"🚫 Заблокировали бота: <b>{final_stats['blocked']}</b>\n"
            f"📈 Успешность: <b>{success_rate}%</b>"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при рассылке: {e}")
        await progress_message.edit_text(
            f"❌ <b>Ошибка при рассылке!</b>\n\n"
            f"Описание: <code>{str(e)}</code>"
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "broadcast_confirm_no")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена")
    await callback.answer()


@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания рассылки"""
    await state.clear()
    await callback.message.edit_text("❌ Создание рассылки отменено")
    await callback.answer()


@router.message(Command("cancel"))
async def cancel_any_state(message: Message, state: FSMContext):
    """Отмена любого состояния"""
    if not is_admin(message.from_user.id):
        return
    
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("❌ Операция отменена")
    else:
        await message.answer("ℹ️ Нет активных операций для отмены")


# Хендлеры для управления сотрудниками

@router.callback_query(F.data == "admin_employees")
async def show_employees_menu(callback: CallbackQuery):
    """Показ меню управления сотрудниками"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    await callback.message.edit_text(
        "👥 <b>Управление сотрудниками</b>\n\n"
        "Выберите действие:",
        reply_markup=AdminKeyboards.employees_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def back_to_admin_menu(callback: CallbackQuery, bot: Bot):
    """Возврат в главное меню админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    # Получаем статистику
    stats = await db.get_bot_stats()
    if not stats:
        stats = await db.update_bot_stats()
    
    total_users = await db.get_users_count()
    active_users = await db.get_active_users_count()
    last_restart = stats.last_restart.strftime("%d.%m.%Y %H:%M:%S")
    
    text = f"""
🔧 <b>Админская панель</b>

📊 <b>Статистика бота:</b>
👥 Всего пользователей: <b>{total_users}</b>
✅ Активных пользователей: <b>{active_users}</b>
🟢 Статус: <b>{stats.status}</b>
🕐 Последний запуск: <b>{last_restart}</b>

Выберите действие:
"""
    
    await callback.message.edit_text(
        text=text,
        reply_markup=AdminKeyboards.main_admin_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "employees_list")
async def show_employees_list(callback: CallbackQuery):
    """Показ списка сотрудников"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    # Получаем всех пользователей
    all_users = await db.get_all_users()
    
    if not all_users:
        await callback.message.edit_text(
            "📋 <b>Список сотрудников</b>\n\n"
            "Сотрудников пока нет.",
            reply_markup=AdminKeyboards.employees_menu()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📋 <b>Список сотрудников</b>\n\n"
        "Выберите сотрудника для просмотра карточки:",
        reply_markup=AdminKeyboards.employees_list_keyboard(all_users)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("employee_view:"))
async def show_employee_card(callback: CallbackQuery):
    """Показ карточки сотрудника"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    user_id = int(callback.data.split(":")[1])
    user = await db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Сотрудник не найден", show_alert=True)
        return
    
    # Формируем информацию о сотруднике
    role_text = "👨‍💼 Администратор" if user.role == "admin" else "👤 Сотрудник"
    status_text = "🔴 Заблокирован" if user.is_blocked else "🟢 Активен"
    full_name = user.full_name or "Не указано"
    username = f"@{user.username}" if user.username else "Не указан"
    created_date = user.created_at.strftime("%d.%m.%Y %H:%M")
    
    # Получаем информацию о том, кто пригласил
    invited_by_text = "Не указано"
    if user.invited_by:
        inviter = await db.get_user(user.invited_by)
        if inviter:
            invited_by_text = inviter.full_name or inviter.first_name or f"ID: {inviter.id}"
    
    text = f"""
👤 <b>Карточка сотрудника</b>

<b>ФИО:</b> {full_name}
<b>Username:</b> {username}
<b>Telegram ID:</b> <code>{user.id}</code>

<b>Роль:</b> {role_text}
<b>Статус:</b> {status_text}

<b>Пригласил:</b> {invited_by_text}
<b>Дата добавления:</b> {created_date}

Выберите действие:
"""
    
    await callback.message.edit_text(
        text=text,
        reply_markup=AdminKeyboards.employee_card_keyboard(user_id, user.is_blocked)
    )
    await callback.answer()


@router.callback_query(F.data == "employee_add")
async def start_add_employee(callback: CallbackQuery, state: FSMContext):
    """Начало добавления сотрудника"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    await state.set_state(AdminStates.add_employee_name)
    
    await callback.message.edit_text(
        "➕ <b>Добавление сотрудника</b>\n\n"
        "Введите ФИО сотрудника:",
        reply_markup=AdminKeyboards.cancel_keyboard("admin_employees")
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.add_employee_name))
async def receive_employee_name(message: Message, state: FSMContext, bot: Bot):
    """Получение ФИО сотрудника и генерация ссылки"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    full_name = message.text.strip()
    
    # Генерируем уникальный код приглашения
    import secrets
    invite_code = secrets.token_urlsafe(16)
    
    # Создаем пригласительную ссылку
    invite_link = await db.create_invite_link(
        code=invite_code,
        created_by=message.from_user.id,
        target_role="employee",
        full_name=full_name
    )
    
    # Формируем ссылку
    bot_username = settings.bot_username or (await bot.get_me()).username
    invite_url = f"https://t.me/{bot_username}?start={invite_code}"
    
    await message.answer(
        f"✅ <b>Пригласительная ссылка создана!</b>\n\n"
        f"<b>ФИО:</b> {full_name}\n"
        f"<b>Ссылка:</b> <code>{invite_url}</code>\n\n"
        f"⚠️ Эта ссылка одноразовая и может быть использована только один раз.\n\n"
        f"Отправьте эту ссылку сотруднику для регистрации в боте.",
        reply_markup=AdminKeyboards.employees_menu()
    )
    
    await state.clear()


@router.callback_query(F.data == "admin_add")
async def start_add_admin(callback: CallbackQuery, state: FSMContext):
    """Начало добавления администратора"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    await state.set_state(AdminStates.add_admin_name)
    
    await callback.message.edit_text(
        "👨‍💼 <b>Добавление администратора</b>\n\n"
        "Введите ФИО администратора:",
        reply_markup=AdminKeyboards.cancel_keyboard("admin_employees")
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.add_admin_name))
async def receive_admin_name(message: Message, state: FSMContext, bot: Bot):
    """Получение ФИО администратора и генерация ссылки"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    full_name = message.text.strip()
    
    # Генерируем уникальный код приглашения
    import secrets
    invite_code = secrets.token_urlsafe(16)
    
    # Создаем пригласительную ссылку для админа
    invite_link = await db.create_invite_link(
        code=invite_code,
        created_by=message.from_user.id,
        target_role="admin",
        full_name=full_name
    )
    
    # Формируем ссылку
    bot_username = settings.bot_username or (await bot.get_me()).username
    invite_url = f"https://t.me/{bot_username}?start={invite_code}"
    
    await message.answer(
        f"✅ <b>Пригласительная ссылка для администратора создана!</b>\n\n"
        f"<b>ФИО:</b> {full_name}\n"
        f"<b>Ссылка:</b> <code>{invite_url}</code>\n\n"
        f"⚠️ Эта ссылка одноразовая и может быть использована только один раз.\n\n"
        f"Отправьте эту ссылку новому администратору для регистрации в боте.",
        reply_markup=AdminKeyboards.employees_menu()
    )
    
    await state.clear()


@router.callback_query(F.data.startswith("employee_block:"))
async def block_employee(callback: CallbackQuery, bot: Bot):
    """Блокировка сотрудника"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    user_id = int(callback.data.split(":")[1])
    
    # Блокируем пользователя
    user = await db.block_user(user_id)
    
    if user:
        await callback.answer("✅ Сотрудник заблокирован", show_alert=True)
        
        # Отправляем уведомление сотруднику
        try:
            admin_name = callback.from_user.full_name or callback.from_user.username or "Администратор"
            await bot.send_message(
                user_id,
                f"🚫 <b>Ваш доступ к боту был заблокирован</b>\n\n"
                f"Администратор <b>{admin_name}</b> заблокировал ваш доступ к боту.\n\n"
                f"Для получения дополнительной информации обратитесь к администратору."
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление о блокировке пользователю {user_id}: {e}")
        
        # Обновляем карточку
        await show_employee_card(callback)
    else:
        await callback.answer("❌ Ошибка блокировки", show_alert=True)


@router.callback_query(F.data.startswith("employee_unblock:"))
async def unblock_employee(callback: CallbackQuery, bot: Bot):
    """Разблокировка сотрудника"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    user_id = int(callback.data.split(":")[1])
    
    # Разблокируем пользователя
    user = await db.unblock_user(user_id)
    
    if user:
        await callback.answer("✅ Сотрудник разблокирован", show_alert=True)
        
        # Отправляем уведомление сотруднику
        try:
            admin_name = callback.from_user.full_name or callback.from_user.username or "Администратор"
            await bot.send_message(
                user_id,
                f"✅ <b>Ваш доступ к боту восстановлен</b>\n\n"
                f"Администратор <b>{admin_name}</b> разблокировал ваш доступ к боту.\n\n"
                f"Теперь вы снова можете использовать все функции бота."
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление о разблокировке пользователю {user_id}: {e}")
        
        # Обновляем карточку
        await show_employee_card(callback)
    else:
        await callback.answer("❌ Ошибка разблокировки", show_alert=True)


@router.callback_query(F.data.startswith("employee_edit:"))
async def start_edit_employee(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования ФИО сотрудника"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    user_id = int(callback.data.split(":")[1])
    
    await state.update_data(edit_user_id=user_id)
    await state.set_state(AdminStates.edit_employee_name)
    
    await callback.message.edit_text(
        "✏️ <b>Редактирование ФИО</b>\n\n"
        "Введите новое ФИО сотрудника:",
        reply_markup=AdminKeyboards.cancel_keyboard(f"employee_view:{user_id}")
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.edit_employee_name))
async def receive_edited_name(message: Message, state: FSMContext):
    """Получение нового ФИО сотрудника"""
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    data = await state.get_data()
    user_id = data.get("edit_user_id")
    new_name = message.text.strip()
    
    # Обновляем ФИО
    user = await db.update_user_full_name(user_id, new_name)
    
    if user:
        await message.answer(
            f"✅ ФИО успешно обновлено на: <b>{new_name}</b>",
            reply_markup=AdminKeyboards.employee_card_keyboard(user_id, user.is_blocked)
        )
    else:
        await message.answer("❌ Ошибка обновления ФИО")
    
    await state.clear()


@router.callback_query(F.data.startswith("employee_reinvite:"))
async def reinvite_employee(callback: CallbackQuery, bot: Bot):
    """Перевыпуск пригласительной ссылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    user_id = int(callback.data.split(":")[1])
    user = await db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Сотрудник не найден", show_alert=True)
        return
    
    # Генерируем новый код приглашения
    import secrets
    invite_code = secrets.token_urlsafe(16)
    
    # Создаем новую пригласительную ссылку
    invite_link = await db.create_invite_link(
        code=invite_code,
        created_by=callback.from_user.id,
        target_role=user.role,
        full_name=user.full_name
    )
    
    # Формируем ссылку
    bot_username = settings.bot_username or (await bot.get_me()).username
    invite_url = f"https://t.me/{bot_username}?start={invite_code}"
    
    await callback.message.answer(
        f"🔗 <b>Новая пригласительная ссылка создана!</b>\n\n"
        f"<b>ФИО:</b> {user.full_name or 'Не указано'}\n"
        f"<b>Ссылка:</b> <code>{invite_url}</code>\n\n"
        f"⚠️ Эта ссылка одноразовая и может быть использована только один раз."
    )
    
    await callback.answer("✅ Ссылка перевыпущена")


@router.callback_query(F.data.startswith("employee_delete_confirm:"))
async def confirm_delete_employee(callback: CallbackQuery):
    """Подтверждение удаления сотрудника"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    user_id = int(callback.data.split(":")[1])
    user = await db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Сотрудник не найден", show_alert=True)
        return
    
    display_name = user.full_name or user.first_name or user.username or f"ID: {user.id}"
    
    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"Вы действительно хотите удалить сотрудника:\n"
        f"<b>{display_name}</b>?\n\n"
        f"Это действие нельзя отменить!",
        reply_markup=AdminKeyboards.employee_delete_confirm(user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("employee_delete:"))
async def delete_employee(callback: CallbackQuery, bot: Bot):
    """Удаление сотрудника"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора")
        return
    
    user_id = int(callback.data.split(":")[1])
    
    # Отправляем уведомление сотруднику ДО удаления
    try:
        admin_name = callback.from_user.full_name or callback.from_user.username or "Администратор"
        await bot.send_message(
            user_id,
            f"🗑 <b>Ваш доступ к боту был удален</b>\n\n"
            f"Администратор <b>{admin_name}</b> удалил вас из системы.\n\n"
            f"Для получения доступа к боту обратитесь к администратору за новой пригласительной ссылкой."
        )
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление об удалении пользователю {user_id}: {e}")
    
    # Удаляем пользователя
    success = await db.delete_user(user_id)
    
    if success:
        await callback.message.edit_text(
            "✅ <b>Сотрудник успешно удален</b>",
            reply_markup=AdminKeyboards.employees_menu()
        )
        await callback.answer()
    else:
        await callback.answer("❌ Ошибка удаления", show_alert=True) 