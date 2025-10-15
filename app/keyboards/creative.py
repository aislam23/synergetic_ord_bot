"""
Клавиатуры для создания креативов
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Формы креативов с их описаниями
CREATIVE_FORMS = {
    "Banner": "Баннер",
    "Text": "Текстовый блок",
    "TextGraphic": "Текст. граф. блок",
    "Video": "Видеоролик",
    "Audio": "Аудиозапись",
    "AudioBroadcast": "Аудиотрансляция",
    "VideoBroadcast": "Видеотрансляции",
    "TextVideoBlock": "Текст. блок с видео",
    "TextAudioBlock": "Текст. блок с аудио",
    "TextAudioVideoBlock": "Текст. блок с аудио и видео",
    "TextGraphicVideoBlock": "Текст. граф. блок с видео",
    "TextGraphicAudioBlock": "Текст. граф. блок с аудио",
    "TextGraphicAudioVideoBlock": "Текст. граф. блок с аудио и видео",
    "BannerHtml5": "HTML5-баннер",
}

# Формы, которые требуют медиа-файл
FORMS_WITH_MEDIA = [
    "Banner", "TextGraphic", "Video", "Audio", "AudioBroadcast",
    "VideoBroadcast", "TextVideoBlock", "TextAudioBlock", 
    "TextAudioVideoBlock", "TextGraphicVideoBlock", 
    "TextGraphicAudioBlock", "TextGraphicAudioVideoBlock", "BannerHtml5"
]

# Формы, которые требуют текст
FORMS_WITH_TEXT = [
    "Text", "TextGraphic", "TextVideoBlock", "TextAudioBlock",
    "TextAudioVideoBlock", "TextGraphicVideoBlock", 
    "TextGraphicAudioBlock", "TextGraphicAudioVideoBlock"
]

# Коды ККТУ (коды товаров, работ, услуг)
KKTU_CODES = {
    "4.1.1": "Средства для мытья посуды",
    "4.1.2": "Средства для стирки",
    "4.1.3": "Чистящие средства",
    "4.1.4": "Моющие и чистящие средства (прочее)",
    "4.2.1": "Средства борьбы с насекомыми",
    "4.3.1": "Средства по уходу за одеждой и обувью",
    "4.3.2": "Бытовая химия (ядохимикаты)",
    "4.3.3": "Бытовая химия (прочее)",
    "15.1.1": "Детский шампунь",
    "15.1.2": "Средства по уходу за волосами",
    "15.1.3": "Шампунь",
    "15.1.4": "Средства по уходу за волосами (прочее)",
    "15.2.1": "Гель для душа",
    "15.2.2": "Мыло",
    "15.2.3": "Средства для бритья и эпиляции (разное)",
    "15.2.4": "Средства для и после бритья",
    "15.2.5": "Средства для удаления волос",
    "15.2.6": "Средства по уходу за кожей",
    "15.3.1": "Дезодоранты",
    "15.3.2": "Декоративная косметика",
    "15.3.3": "Парфюмерия",
    "15.3.4": "Средства по уходу за ногтями",
    "15.3.5": "Товары для красоты и здоровья (разное)",
    "22.2.3": "Подгузники",
    "22.2.4": "Средства гигиены для детей",
    "22.2.5": "Средства и предметы гигиены (прочее)",
    "22.3.1": "Зубная паста",
    "22.3.2": "Зубные щетки",
    "22.3.3": "Средства для гигиены рта",
    "22.3.4": "Средства гигиены (прочее)",
    "26.3.1": "Средства детской гигиены",
}


def get_creative_forms_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора формы креатива"""
    builder = InlineKeyboardBuilder()
    
    for code, description in CREATIVE_FORMS.items():
        builder.button(
            text=description,
            callback_data=f"form:{code}"
        )
    
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()


def get_kktu_keyboard(page: int = 0, items_per_page: int = 10) -> InlineKeyboardMarkup:
    """Клавиатура для выбора кода ККТУ с пагинацией"""
    builder = InlineKeyboardBuilder()
    
    # Получаем список кодов
    codes_list = list(KKTU_CODES.items())
    total_pages = (len(codes_list) + items_per_page - 1) // items_per_page
    
    # Получаем элементы для текущей страницы
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = codes_list[start_idx:end_idx]
    
    # Добавляем кнопки кодов ККТУ
    for code, description in page_items:
        # Ограничиваем длину описания
        short_desc = description[:35] + "..." if len(description) > 35 else description
        builder.button(
            text=f"{code} - {short_desc}",
            callback_data=f"kktu:{code}"
        )
    
    builder.adjust(1)  # По одной кнопке в ряд
    
    # Добавляем навигационные кнопки
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"kktu_page:{page-1}"
        ))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперёд ➡️",
            callback_data=f"kktu_page:{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Добавляем индикатор страницы
    builder.row(InlineKeyboardButton(
        text=f"📄 Страница {page + 1} из {total_pages}",
        callback_data="page_info"
    ))
    
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения создания креатива"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Создать креатив", callback_data="confirm:yes")
    builder.button(text="❌ Отменить", callback_data="confirm:no")
    
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🎨 Создать креатив", callback_data="create_creative")
    builder.button(text="📋 Мои креативы", callback_data="my_creatives")
    builder.button(text="ℹ️ Помощь", callback_data="help")
    
    builder.adjust(1)
    return builder.as_markup()


def get_skip_text_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для пропуска текста (если текст не обязателен)"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="⏭ Пропустить", callback_data="skip_text")
    
    return builder.as_markup()


def get_navigation_keyboard(
    show_back: bool = True,
    show_skip: bool = False,
    back_callback: str = "nav:back",
    skip_callback: str = "nav:skip"
) -> InlineKeyboardMarkup:
    """
    Универсальная клавиатура навигации для этапов создания креатива
    
    Args:
        show_back: показывать ли кнопку "Назад"
        show_skip: показывать ли кнопку "Пропустить"
        back_callback: callback для кнопки "Назад"
        skip_callback: callback для кнопки "Пропустить"
    """
    builder = InlineKeyboardBuilder()
    
    buttons = []
    
    if show_skip:
        buttons.append(InlineKeyboardButton(
            text="⏭ Пропустить",
            callback_data=skip_callback
        ))
    
    if show_back:
        buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=back_callback
        ))
    
    buttons.append(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data="nav:cancel"
    ))
    
    # Размещаем кнопки
    if len(buttons) == 3 and show_skip:
        # Если есть все три кнопки: Пропустить, Назад, Отменить
        builder.row(buttons[0])  # Пропустить
        builder.row(buttons[1], buttons[2])  # Назад и Отменить в ряд
    elif len(buttons) == 2:
        # Если две кнопки: Назад и Отменить
        builder.row(*buttons)
    else:
        # В остальных случаях
        for button in buttons:
            builder.row(button)
    
    return builder.as_markup()


def get_form_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора формы креатива с кнопкой отмены"""
    builder = InlineKeyboardBuilder()
    
    for code, description in CREATIVE_FORMS.items():
        builder.button(
            text=description,
            callback_data=f"form:{code}"
        )
    
    # Разбиваем на две колонки
    builder.adjust(2)
    
    # Добавляем только кнопку отмены (без "Назад", т.к. это первый шаг)
    builder.row(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data="nav:cancel"
    ))
    
    return builder.as_markup()


def get_kktu_keyboard_with_nav(page: int = 0, items_per_page: int = 10, show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора кода ККТУ с пагинацией и навигацией"""
    builder = InlineKeyboardBuilder()
    
    # Получаем список кодов
    codes_list = list(KKTU_CODES.items())
    total_pages = (len(codes_list) + items_per_page - 1) // items_per_page
    
    # Получаем элементы для текущей страницы
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = codes_list[start_idx:end_idx]
    
    # Добавляем кнопки кодов ККТУ
    for code, description in page_items:
        # Ограничиваем длину описания
        short_desc = description[:35] + "..." if len(description) > 35 else description
        builder.button(
            text=f"{code} - {short_desc}",
            callback_data=f"kktu:{code}"
        )
    
    builder.adjust(1)  # По одной кнопке в ряд
    
    # Добавляем навигационные кнопки для пагинации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Предыдущая",
            callback_data=f"kktu_page:{page-1}"
        ))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="Следующая ➡️",
            callback_data=f"kktu_page:{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Добавляем индикатор страницы
    builder.row(InlineKeyboardButton(
        text=f"📄 Страница {page + 1} из {total_pages}",
        callback_data="page_info"
    ))
    
    # Добавляем кнопки навигации (Назад и Отменить)
    nav_row = []
    if show_back:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="nav:back"
        ))
    nav_row.append(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data="nav:cancel"
    ))
    builder.row(*nav_row)
    
    return builder.as_markup()


def get_confirm_keyboard_with_nav() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения создания креатива с навигацией"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Создать креатив", callback_data="confirm:yes")
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="nav:back"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="nav:cancel")
    )
    
    builder.adjust(1)
    return builder.as_markup()

