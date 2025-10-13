"""
Клавиатуры для создания креативов
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Формы креативов с их описаниями
CREATIVE_FORMS = {
    "Banner": "Баннер",
    "Text": "Текстовый блок",
    "TextGraphic": "Текстово-графический блок",
    "Video": "Видеоролик",
    "Audio": "Аудиозапись",
    "AudioBroadcast": "Аудиотрансляции в прямом эфире",
    "VideoBroadcast": "Видеотрансляции в прямом эфире",
    "TextVideoBlock": "Текстовый блок с видео",
    "TextAudioBlock": "Текстовый блок с аудио",
    "TextAudioVideoBlock": "Текстовый блок с аудио и видео",
    "TextGraphicVideoBlock": "Текстово-графический блок с видео",
    "TextGraphicAudioBlock": "Текстово-графический блок с аудио",
    "TextGraphicAudioVideoBlock": "Текстово-графический блок с аудио и видео",
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

# Основные категории ККТУ (коды 3 уровня)
KKTU_CODES = {
    "1.1.1": "Алкогольная продукция крепостью свыше 15%",
    "1.1.2": "Алкогольная продукция крепостью до 15%",
    "1.2.1": "Пиво и пивные напитки",
    "1.3.1": "Табачная продукция",
    "1.3.2": "Никотинсодержащая продукция",
    "2.1.1": "Лекарственные препараты",
    "2.2.1": "Медицинские изделия",
    "2.2.2": "Медицинские услуги",
    "3.1.1": "Азартные игры",
    "3.2.1": "Лотереи",
    "4.1.1": "Ценные бумаги",
    "4.1.2": "Банковские услуги",
    "4.1.3": "Страховые услуги",
    "4.2.1": "Инвестиционные услуги",
    "5.1.1": "Оружие и патроны",
    "6.1.1": "Биологически активные добавки",
    "7.1.1": "Услуги по привлечению денежных средств",
    "8.1.1": "Услуги экстрасенсов, магов, гадалок",
    "30.1.1": "Пищевые продукты",
    "30.1.2": "Напитки безалкогольные",
    "30.2.1": "Одежда и обувь",
    "30.2.2": "Текстильные изделия",
    "30.3.1": "Мебель и товары для дома",
    "30.4.1": "Бытовая техника и электроника",
    "30.5.1": "Косметика и парфюмерия",
    "30.6.1": "Товары для детей",
    "30.7.1": "Спортивные товары",
    "30.8.1": "Книги и канцелярские товары",
    "30.9.1": "Товары для животных",
    "30.10.1": "Строительные материалы",
    "30.11.1": "Автотовары и запчасти",
    "30.12.1": "Туризм и отдых",
    "30.13.1": "Образовательные услуги",
    "30.14.1": "Развлекательные услуги",
    "30.15.1": "Информационные услуги и сервисы",
    "30.16.1": "Услуги связи",
    "30.17.1": "Транспортные услуги",
    "30.18.1": "Услуги общественного питания",
    "30.19.1": "Недвижимость",
    "30.20.1": "Прочие товары и услуги",
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

