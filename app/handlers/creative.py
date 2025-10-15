"""
Обработчики для создания креативов
"""
import base64
import re
from io import BytesIO
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.states.creative import CreativeStates
from app.keyboards.creative import (
    get_creative_forms_keyboard,
    get_kktu_keyboard,
    get_confirm_keyboard,
    get_main_menu_keyboard,
    get_navigation_keyboard,
    get_form_selection_keyboard,
    get_kktu_keyboard_with_nav,
    get_confirm_keyboard_with_nav,
    FORMS_WITH_MEDIA,
    FORMS_WITH_TEXT,
    CREATIVE_FORMS,
    KKTU_CODES
)
from app.services.mediascout import mediascout_api
from app.database import db

router = Router()


# Валидация URL
def validate_url(url: str) -> bool:
    """Проверка корректности URL"""
    # Проверка протокола http или https
    url_pattern = re.compile(
        r'^https?://'  # http:// или https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # доменное имя
        r'localhost|'  # или localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # или IP
        r'(?::\d+)?'  # опциональный порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


@router.message(Command("menu"))
async def show_menu(message: Message):
    """Показать главное меню"""
    await message.answer(
        "🎨 <b>Главное меню</b>\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "create_creative")
async def start_creative_creation(callback: CallbackQuery, state: FSMContext):
    """Начать процесс создания креатива"""
    await callback.answer()
    
    # Очищаем предыдущее состояние
    await state.clear()
    
    await callback.message.edit_text(
        "🎨 <b>Создание креатива для саморекламы</b>\n\n"
        "Выберите форму креатива:",
        reply_markup=get_form_selection_keyboard()
    )
    await state.set_state(CreativeStates.select_form)


# ============ ОБРАБОТЧИКИ НАВИГАЦИИ ============

@router.callback_query(F.data == "nav:cancel")
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена создания креатива"""
    await callback.answer()
    
    await callback.message.edit_text(
        "❌ Создание креатива отменено.\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Очищаем состояние
    await state.clear()


@router.callback_query(F.data == "nav:back")
async def handle_back(callback: CallbackQuery, state: FSMContext):
    """Возврат на предыдущий шаг"""
    await callback.answer()
    
    current_state = await state.get_state()
    data = await state.get_data()
    form_code = data.get("form")
    
    # Определяем предыдущий шаг в зависимости от текущего состояния
    if current_state == CreativeStates.upload_media:
        # С загрузки медиа возвращаемся к выбору формы
        await callback.message.edit_text(
            "🎨 <b>Создание креатива для саморекламы</b>\n\n"
            "Выберите форму креатива:",
            reply_markup=get_form_selection_keyboard()
        )
        await state.set_state(CreativeStates.select_form)
        # Очищаем данные о форме
        await state.update_data(form=None, form_name=None)
    
    elif current_state == CreativeStates.enter_text:
        # С ввода текста возвращаемся либо к медиа, либо к форме
        if form_code and form_code in FORMS_WITH_MEDIA:
            # Возвращаемся к загрузке медиа
            form_name = data.get('form_name', form_code)
            await callback.message.edit_text(
                f"📎 <b>Форма: {form_name}</b>\n\n"
                "Загрузите медиа-файл (фото, видео, аудио или документ):",
                reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
            )
            await state.set_state(CreativeStates.upload_media)
            # Очищаем данные о медиа
            await state.update_data(media_file_id=None, media_file_name=None, media_base64=None)
        else:
            # Возвращаемся к выбору формы
            await callback.message.edit_text(
                "🎨 <b>Создание креатива для саморекламы</b>\n\n"
                "Выберите форму креатива:",
                reply_markup=get_form_selection_keyboard()
            )
            await state.set_state(CreativeStates.select_form)
            await state.update_data(form=None, form_name=None)
    
    elif current_state == CreativeStates.enter_advertiser_urls:
        # С ввода URL возвращаемся к тексту или медиа
        if form_code and form_code in FORMS_WITH_TEXT:
            # Возвращаемся к вводу текста
            form_name = data.get('form_name', form_code)
            await callback.message.edit_text(
                f"📝 <b>Форма: {form_name}</b>\n\n"
                "Введите текст креатива:",
                reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
            )
            await state.set_state(CreativeStates.enter_text)
            # Очищаем данные о тексте
            await state.update_data(text_data=None)
        elif form_code and form_code in FORMS_WITH_MEDIA:
            # Возвращаемся к загрузке медиа
            form_name = data.get('form_name', form_code)
            await callback.message.edit_text(
                f"📎 <b>Форма: {form_name}</b>\n\n"
                "Загрузите медиа-файл (фото, видео, аудио или документ):",
                reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
            )
            await state.set_state(CreativeStates.upload_media)
            await state.update_data(media_file_id=None, media_file_name=None, media_base64=None)
        else:
            # Возвращаемся к выбору формы
            await callback.message.edit_text(
                "🎨 <b>Создание креатива для саморекламы</b>\n\n"
                "Выберите форму креатива:",
                reply_markup=get_form_selection_keyboard()
            )
            await state.set_state(CreativeStates.select_form)
            await state.update_data(form=None, form_name=None)
    
    elif current_state == CreativeStates.select_kktu:
        # С выбора ККТУ возвращаемся к вводу URL
        await callback.message.edit_text(
            "🔗 <b>Целевые ссылки (advertiserUrls)</b>\n\n"
            "Введите целевые ссылки (URL) через запятую или с новой строки.\n"
            "Например:\n"
            "<code>https://example.com, https://test.ru</code>\n\n"
            "⚠️ Поддерживаются только протоколы http и https.\n"
            "💡 Это поле необязательное, можно пропустить.",
            reply_markup=get_navigation_keyboard(show_back=True, show_skip=True, skip_callback="nav:skip_urls")
        )
        await state.set_state(CreativeStates.enter_advertiser_urls)
        # Очищаем данные о ККТУ
        await state.update_data(kktu_code=None, kktu_name=None)
    
    elif current_state == CreativeStates.confirm_creation:
        # С подтверждения возвращаемся к выбору ККТУ
        await callback.message.edit_text(
            "Выберите код ККТУ (категорию товара/услуги):",
            reply_markup=get_kktu_keyboard_with_nav(page=0, show_back=True)
        )
        await state.set_state(CreativeStates.select_kktu)


@router.callback_query(F.data.startswith("form:"), CreativeStates.select_form)
async def form_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора формы креатива"""
    await callback.answer()
    
    form_code = callback.data.split(":")[1]
    form_name = CREATIVE_FORMS.get(form_code, form_code)
    
    # Сохраняем выбранную форму
    await state.update_data(form=form_code, form_name=form_name)
    
    # Проверяем, требуется ли медиа-файл
    if form_code in FORMS_WITH_MEDIA:
        await callback.message.edit_text(
            f"📎 <b>Форма: {form_name}</b>\n\n"
            "Загрузите медиа-файл (фото, видео, аудио или документ):",
            reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
        )
        await state.set_state(CreativeStates.upload_media)
    # Проверяем, требуется ли текст
    elif form_code in FORMS_WITH_TEXT:
        await callback.message.edit_text(
            f"📝 <b>Форма: {form_name}</b>\n\n"
            "Введите текст креатива:",
            reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
        )
        await state.set_state(CreativeStates.enter_text)
    else:
        # Если не требуется ни медиа, ни текст - переходим к URL
        await callback.message.edit_text(
            "🔗 <b>Целевые ссылки (advertiserUrls)</b>\n\n"
            "Введите целевые ссылки (URL) через запятую или с новой строки.\n"
            "Например:\n"
            "<code>https://example.com, https://test.ru</code>\n\n"
            "⚠️ Поддерживаются только протоколы http и https.\n"
            "💡 Это поле необязательное, можно пропустить.",
            reply_markup=get_navigation_keyboard(show_back=True, show_skip=True, skip_callback="nav:skip_urls")
        )
        await state.set_state(CreativeStates.enter_advertiser_urls)


@router.message(CreativeStates.upload_media, F.photo | F.video | F.audio | F.document)
async def media_uploaded(message: Message, state: FSMContext):
    """Обработка загрузки медиа-файла"""
    
    data = await state.get_data()
    form_code = data.get("form")
    
    # Получаем file_id и информацию о файле
    file_id = None
    file_name = None
    file_obj = None
    file_type = None
    
    if message.photo:
        # Берем фото наибольшего размера
        file_obj = message.photo[-1]
        file_id = file_obj.file_id
        file_name = f"photo_{file_id}.jpg"
        file_type = "фото"
    elif message.video:
        file_obj = message.video
        file_id = file_obj.file_id
        file_name = message.video.file_name or f"video_{file_id}.mp4"
        file_type = "видео"
    elif message.audio:
        file_obj = message.audio
        file_id = file_obj.file_id
        file_name = message.audio.file_name or f"audio_{file_id}.mp3"
        file_type = "аудио"
    elif message.document:
        file_obj = message.document
        file_id = file_obj.file_id
        file_name = message.document.file_name or f"document_{file_id}"
        file_type = "документ"
    
    if not file_id:
        await message.answer(
            "❌ Ошибка: не удалось получить файл. Попробуйте снова.",
            reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
        )
        return
    
    # Показываем индикацию начала обработки
    processing_msg = await message.answer(
        f"📥 Получено {file_type}: <code>{file_name}</code>\n"
        "⏳ Обработка файла..."
    )
    
    # Скачиваем файл
    try:
        file = await message.bot.get_file(file_id)
        file_bytes = BytesIO()
        await message.bot.download_file(file.file_path, file_bytes)
        
        # Конвертируем в base64
        file_base64 = base64.b64encode(file_bytes.getvalue()).decode('utf-8')
        
        # Получаем размер файла
        file_size = len(file_bytes.getvalue())
        file_size_mb = file_size / (1024 * 1024)
        
        # Сохраняем данные
        await state.update_data(
            media_file_id=file_id,
            media_file_name=file_name,
            media_base64=file_base64
        )
        
        # Удаляем сообщение о обработке
        await processing_msg.delete()
        
        # Проверяем, нужен ли еще текст
        if form_code in FORMS_WITH_TEXT:
            await message.answer(
                f"✅ Медиа-файл загружен и обработан\n\n"
                f"📎 <b>Файл:</b> <code>{file_name}</code>\n"
                f"📊 <b>Размер:</b> {file_size_mb:.2f} МБ\n\n"
                "📝 Теперь введите текст креатива:",
                reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
            )
            await state.set_state(CreativeStates.enter_text)
        else:
            # Если текст не нужен, переходим к URL
            await message.answer(
                f"✅ Медиа-файл загружен и обработан\n\n"
                f"📎 <b>Файл:</b> <code>{file_name}</code>\n"
                f"📊 <b>Размер:</b> {file_size_mb:.2f} МБ\n\n"
                "🔗 <b>Целевые ссылки</b>\n\n"
                "Отправьте целевые ссылки (URL), которые будут в креативе.\n"
                "Через запятую или с новой строки.\n"
                "Например:\n"
                "<code>https://example.com, https://test.ru</code>\n\n"
                "⚠️ Ссылки должны начинаться с http или https.\n"
                "💡 Это поле необязательное, можно пропустить.",
                reply_markup=get_navigation_keyboard(show_back=True, show_skip=True, skip_callback="nav:skip_urls")
            )
            await state.set_state(CreativeStates.enter_advertiser_urls)
    
    except Exception as e:
        logger.error(f"Ошибка при обработке медиа-файла: {e}")
        # Пытаемся удалить сообщение о обработке
        try:
            await processing_msg.delete()
        except:
            pass
        
        await message.answer(
            "❌ Ошибка при загрузке файла. Попробуйте снова или выберите другой файл.",
            reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
        )


@router.message(CreativeStates.upload_media)
async def invalid_media(message: Message):
    """Обработка неверного типа медиа"""
    await message.answer(
        "❌ Пожалуйста, отправьте медиа-файл (фото, видео, аудио).",
        reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
    )


@router.message(CreativeStates.enter_text, F.text)
async def text_entered(message: Message, state: FSMContext):
    """Обработка ввода текста"""
    
    text = message.text.strip()
    
    if len(text) < 1 or len(text) > 1000:
        await message.answer(
            "❌ Текст должен быть от 1 до 1000 символов. Попробуйте снова.",
            reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
        )
        return
    
    # Сохраняем текст
    await state.update_data(text_data=text)
    
    # Переходим к вводу URL
    await message.answer(
        f"✅ Текст сохранен ({len(text)} символов)\n\n"
        "🔗 <b>Целевые ссылки</b>\n\n"
        "Отправьте целевые ссылки (URL), которые будут в креативе.\n"
        "Через запятую или с новой строки.\n"
        "Например:\n"
        "<code>https://example.com, https://test.ru</code>\n\n"
        "⚠️ Ссылки должны начинаться с http или https.\n"
        "💡 Это поле необязательное, можно пропустить.",
        reply_markup=get_navigation_keyboard(show_back=True, show_skip=True, skip_callback="nav:skip_urls")
    )
    await state.set_state(CreativeStates.enter_advertiser_urls)


@router.message(CreativeStates.enter_text)
async def invalid_text(message: Message):
    """Обработка неверного ввода текста"""
    await message.answer(
        "❌ Пожалуйста, отправьте текстовое сообщение.",
        reply_markup=get_navigation_keyboard(show_back=True, show_skip=False)
    )


# ============ ОБРАБОТЧИКИ ADVERTISER URLS ============

@router.callback_query(F.data == "nav:skip_urls", CreativeStates.enter_advertiser_urls)
async def skip_advertiser_urls(callback: CallbackQuery, state: FSMContext):
    """Пропуск ввода целевых ссылок"""
    await callback.answer("Целевые ссылки пропущены")
    
    # Переходим к выбору ККТУ
    await callback.message.edit_text(
        "Выберите категорию товара/услуги (ККТУ):",
        reply_markup=get_kktu_keyboard_with_nav(page=0, show_back=True)
    )
    await state.set_state(CreativeStates.select_kktu)


@router.message(CreativeStates.enter_advertiser_urls, F.text)
async def advertiser_urls_entered(message: Message, state: FSMContext):
    """Обработка ввода целевых ссылок"""
    
    text = message.text.strip()
    
    # Разбиваем по запятым и новым строкам
    urls = []
    for line in text.split('\n'):
        for url in line.split(','):
            url = url.strip()
            if url:
                urls.append(url)
    
    # Валидация URL
    invalid_urls = []
    valid_urls = []
    
    for url in urls:
        if validate_url(url):
            valid_urls.append(url)
        else:
            invalid_urls.append(url)
    
    if invalid_urls:
        # Есть невалидные URL
        error_text = "❌ Некоторые URL некорректны:\n\n"
        for url in invalid_urls[:5]:  # Показываем первые 5
            error_text += f"• <code>{url}</code>\n"
        if len(invalid_urls) > 5:
            error_text += f"\n...и ещё {len(invalid_urls) - 5}\n"
        error_text += "\n⚠️ URL должны начинаться с http:// или https://\n"
        error_text += "Попробуйте снова или пропустите этот шаг."
        
        await message.answer(
            error_text,
            reply_markup=get_navigation_keyboard(show_back=True, show_skip=True, skip_callback="nav:skip_urls")
        )
        return
    
    if not valid_urls:
        await message.answer(
            "❌ Не найдено ни одного корректного URL. Попробуйте снова или пропустите этот шаг.",
            reply_markup=get_navigation_keyboard(show_back=True, show_skip=True, skip_callback="nav:skip_urls")
        )
        return
    
    # Сохраняем валидные URL
    await state.update_data(advertiser_urls=valid_urls)
    
    # Переходим к выбору ККТУ
    await message.answer(
        f"✅ Сохранено целевых ссылок: {len(valid_urls)}\n\n"
        "Выберите категорию товара/услуги (ККТУ):",
        reply_markup=get_kktu_keyboard_with_nav(page=0, show_back=True)
    )
    await state.set_state(CreativeStates.select_kktu)


@router.message(CreativeStates.enter_advertiser_urls)
async def invalid_advertiser_urls(message: Message):
    """Обработка неверного ввода URL"""
    await message.answer(
        "❌ Пожалуйста, отправьте текстовое сообщение с URL.",
        reply_markup=get_navigation_keyboard(show_back=True, show_skip=True, skip_callback="nav:skip_urls")
    )


@router.callback_query(F.data.startswith("kktu_page:"), CreativeStates.select_kktu)
async def kktu_page_navigation(callback: CallbackQuery, state: FSMContext):
    """Навигация по страницам ККТУ"""
    await callback.answer()
    
    page = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "Выберите категорию товара/услуги (ККТУ):",
        reply_markup=get_kktu_keyboard_with_nav(page=page, show_back=True)
    )


@router.callback_query(F.data == "page_info", CreativeStates.select_kktu)
async def page_info_handler(callback: CallbackQuery):
    """Обработчик нажатия на индикатор страницы"""
    await callback.answer("Используйте кнопки навигации для переключения страниц")


@router.callback_query(F.data.startswith("kktu:"), CreativeStates.select_kktu)
async def kktu_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории товара/услуги (ККТУ)"""
    await callback.answer()
    
    kktu_code = callback.data.split(":")[1]
    kktu_name = KKTU_CODES.get(kktu_code, kktu_code)
    
    # Сохраняем выбранную категорию товара/услуги (ККТУ)
    await state.update_data(kktu_code=kktu_code, kktu_name=kktu_name)
    
    # Получаем все данные для подтверждения
    data = await state.get_data()
    
    # Формируем сообщение подтверждения
    confirmation_text = "📋 <b>Подтвердите данные креатива</b>\n\n"
    confirmation_text += f"🎨 <b>Форма:</b> {data.get('form_name')}\n"
    confirmation_text += f"📦 <b>Категория товара/услуги (ККТУ):</b> {kktu_code} - {kktu_name}\n"
    
    if data.get('text_data'):
        text_preview = data['text_data'][:100] + "..." if len(data['text_data']) > 100 else data['text_data']
        confirmation_text += f"📝 <b>Текст:</b> {text_preview}\n"
    
    if data.get('media_file_name'):
        confirmation_text += f"📎 <b>Медиа:</b> {data['media_file_name']}\n"
    
    if data.get('advertiser_urls'):
        urls_count = len(data['advertiser_urls'])
        confirmation_text += f"🔗 <b>Целевые ссылки:</b> {urls_count} шт.\n"
        # Показываем первую ссылку как пример
        if urls_count > 0:
            first_url = data['advertiser_urls'][0]
            if len(first_url) > 50:
                first_url = first_url[:47] + "..."
            confirmation_text += f"   • {first_url}\n"
            if urls_count > 1:
                confirmation_text += f"   • ...и ещё {urls_count - 1}\n"
    
    confirmation_text += "\n⚠️ <b>Параметры по умолчанию:</b>\n"
    confirmation_text += "• Тип: Саморекламa (isSelfPromotion = true)\n"
    confirmation_text += "• Тип кампании: Other\n\n"
    confirmation_text += "Создать креатив?"
    
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=get_confirm_keyboard_with_nav()
    )
    await state.set_state(CreativeStates.confirm_creation)


@router.callback_query(F.data == "confirm:yes", CreativeStates.confirm_creation)
async def confirm_creation(callback: CallbackQuery, state: FSMContext):
    """Подтверждение создания креатива"""
    await callback.answer()
    
    # Показываем индикатор загрузки
    await callback.message.edit_text(
        "⏳ Создание креатива...\n"
        "Пожалуйста, подождите."
    )
    
    # Получаем все данные
    data = await state.get_data()
    
    # Создаем креатив через API
    result = await mediascout_api.create_creative(
        form=data['form'],
        kktu_code=data['kktu_code'],
        media_base64=data.get('media_base64'),
        media_filename=data.get('media_file_name'),
        text_data=data.get('text_data'),
        description=data.get('text_data') if data['kktu_code'] == '30.15.1' else None,
        advertiser_urls=data.get('advertiser_urls')
    )
    
    if result.get('success'):
        # Успешное создание
        erid = result.get('erid')
        
        # Сохраняем в базу данных
        try:
            await db.save_creative(
                user_id=callback.from_user.id,
                form=data['form'],
                kktu_code=data['kktu_code'],
                erid=erid,
                media_file_id=data.get('media_file_id'),
                media_file_name=data.get('media_file_name'),
                text_data=data.get('text_data'),
                mediascout_id=result.get('id'),
                creative_group_id=result.get('creative_group_id'),
                creative_group_name=result.get('creative_group_name'),
                status="created"
            )
            logger.info(f"✅ Креатив сохранен в БД: {erid}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения креатива в БД: {e}")
        
        success_text = "✅ <b>Креатив успешно создан!</b>\n\n"
        success_text += f"🎫 <b>Токен Erid:</b>\n<code>{erid}</code>\n\n"
        success_text += f"📋 <b>Форма:</b> {data.get('form_name')}\n"
        success_text += f"📦 <b>Категория товара/услуги (ККТУ):</b> {data.get('kktu_code')} - {data.get('kktu_name')}\n\n"
        success_text += "💡 <i>Чтобы скопировать токен Erid, нажмите на него</i>"
        
        await callback.message.edit_text(
            success_text,
            reply_markup=get_main_menu_keyboard()
        )
        
        # Очищаем состояние
        await state.clear()
        
    else:
        # Ошибка создания
        error_msg = result.get('error', 'Неизвестная ошибка')
        
        error_text = "❌ <b>Ошибка при создании креатива</b>\n\n"
        error_text += f"📝 <b>Детали:</b> {error_msg}\n\n"
        error_text += "Попробуйте снова или обратитесь в поддержку."
        
        await callback.message.edit_text(
            error_text,
            reply_markup=get_main_menu_keyboard()
        )
        
        # Очищаем состояние
        await state.clear()




@router.callback_query(F.data == "my_creatives")
async def show_my_creatives(callback: CallbackQuery):
    """Показать мои креативы"""
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Получаем креативы пользователя
    creatives = await db.get_user_creatives(user_id, limit=10)
    total_count = await db.get_user_creatives_count(user_id)
    
    if not creatives:
        await callback.message.edit_text(
            "📋 <b>Мои креативы</b>\n\n"
            "У вас пока нет созданных креативов.\n"
            "Нажмите \"🎨 Создать креатив\" чтобы начать.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Формируем список креативов
    text = f"📋 <b>Мои креативы</b> (всего: {total_count})\n\n"
    
    for idx, creative in enumerate(creatives, 1):
        status_emoji = "✅" if creative.status == "created" else "❌"
        text += f"{status_emoji} <b>Креатив #{creative.id}</b>\n"
        text += f"   🎨 Форма: {CREATIVE_FORMS.get(creative.form, creative.form)}\n"
        text += f"   📦 Категория товара/услуги (ККТУ): {creative.kktu_code}\n"
        
        if creative.erid:
            text += f"   🎫 Erid: <code>{creative.erid}</code>\n"
        
        if creative.status == "error" and creative.error_message:
            text += f"   ❌ Ошибка: {creative.error_message[:50]}...\n"
        
        text += f"   📅 Создан: {creative.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    if total_count > 10:
        text += f"<i>Показаны последние 10 из {total_count} креативов</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показать помощь"""
    await callback.answer()
    
    help_text = """
ℹ️ <b>Помощь по работе с ботом</b>

<b>Что такое Erid?</b>
Erid (маркер) — уникальный идентификатор рекламы, который должен быть указан в каждом рекламном креативе согласно закону о рекламе.

<b>Как создать креатив?</b>
1. Нажмите "🎨 Создать креатив"
2. Выберите форму креатива (баннер, текст, видео и т.д.)
3. Загрузите медиа-файл (если требуется)
4. Введите текст (если требуется)
5. Выберите категорию товара/услуги (ККТУ)
6. Подтвердите создание
7. Получите токен Erid

<b>Саморекламa</b>
Этот бот создает креативы саморекламы, которые не требуют договоров между сторонами.

<b>Техподдержка</b>
По вопросам работы бота обращайтесь к администратору.
"""
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_main_menu_keyboard()
    )

