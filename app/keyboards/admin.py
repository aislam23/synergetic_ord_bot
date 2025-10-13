"""
Клавиатуры для админской части
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminKeyboards:
    """Клавиатуры для админской панели"""
    
    @staticmethod
    def main_admin_menu() -> InlineKeyboardMarkup:
        """Главное меню админа"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="👥 Управление сотрудниками",
            callback_data="admin_employees"
        ))
        
        builder.add(InlineKeyboardButton(
            text="📊 Рассылка",
            callback_data="admin_broadcast"
        ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def broadcast_confirm(message_count: int) -> InlineKeyboardMarkup:
        """Подтверждение рассылки"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text=f"✅ Отправить ({message_count} польз.)",
            callback_data="broadcast_confirm_yes"
        ))
        
        builder.add(InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="broadcast_confirm_no"
        ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def broadcast_add_button() -> InlineKeyboardMarkup:
        """Меню добавления кнопки к рассылке"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="➕ Добавить кнопку",
            callback_data="broadcast_add_button"
        ))
        
        builder.add(InlineKeyboardButton(
            text="📤 Отправить без кнопки",
            callback_data="broadcast_no_button"
        ))
        
        builder.add(InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="broadcast_cancel"
        ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def broadcast_button_confirm() -> InlineKeyboardMarkup:
        """Подтверждение кнопки для рассылки"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data="broadcast_button_confirm"
        ))
        
        builder.add(InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="broadcast_cancel"
        ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def create_custom_button(text: str, url: str) -> InlineKeyboardMarkup:
        """Создание кастомной кнопки для рассылки"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text=text,
            url=url
        ))
        
        return builder.as_markup()
    
    # Клавиатуры для управления сотрудниками
    
    @staticmethod
    def employees_menu() -> InlineKeyboardMarkup:
        """Меню управления сотрудниками"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="📋 Список сотрудников",
            callback_data="employees_list"
        ))
        
        builder.add(InlineKeyboardButton(
            text="➕ Добавить сотрудника",
            callback_data="employee_add"
        ))
        
        builder.add(InlineKeyboardButton(
            text="👨‍💼 Добавить администратора",
            callback_data="admin_add"
        ))
        
        builder.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="admin_back"
        ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def employees_list_keyboard(employees: list) -> InlineKeyboardMarkup:
        """Список сотрудников с инлайн-кнопками"""
        builder = InlineKeyboardBuilder()
        
        for employee in employees:
            # Формируем текст кнопки с иконками статуса
            status_icon = "🔴" if employee.is_blocked else "🟢"
            role_icon = "👨‍💼" if employee.role == "admin" else "👤"
            
            display_name = employee.full_name or employee.first_name or employee.username or f"ID: {employee.id}"
            
            builder.add(InlineKeyboardButton(
                text=f"{role_icon} {status_icon} {display_name}",
                callback_data=f"employee_view:{employee.id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="admin_employees"
        ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def employee_card_keyboard(user_id: int, is_blocked: bool) -> InlineKeyboardMarkup:
        """Карточка сотрудника с кнопками управления"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="✏️ Редактировать ФИО",
            callback_data=f"employee_edit:{user_id}"
        ))
        
        # Кнопка блокировки/разблокировки
        if is_blocked:
            builder.add(InlineKeyboardButton(
                text="✅ Разблокировать",
                callback_data=f"employee_unblock:{user_id}"
            ))
        else:
            builder.add(InlineKeyboardButton(
                text="🚫 Заблокировать",
                callback_data=f"employee_block:{user_id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="🔗 Перевыпустить ссылку",
            callback_data=f"employee_reinvite:{user_id}"
        ))
        
        builder.add(InlineKeyboardButton(
            text="🗑 Удалить сотрудника",
            callback_data=f"employee_delete_confirm:{user_id}"
        ))
        
        builder.add(InlineKeyboardButton(
            text="🔙 К списку",
            callback_data="employees_list"
        ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def employee_delete_confirm(user_id: int) -> InlineKeyboardMarkup:
        """Подтверждение удаления сотрудника"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"employee_delete:{user_id}"
        ))
        
        builder.add(InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"employee_view:{user_id}"
        ))
        
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def cancel_keyboard(back_to: str = "admin_employees") -> InlineKeyboardMarkup:
        """Клавиатура отмены"""
        builder = InlineKeyboardBuilder()
        
        builder.add(InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=back_to
        ))
        
        return builder.as_markup() 