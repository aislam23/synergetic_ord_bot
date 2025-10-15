"""
Состояния для создания креативов
"""
from aiogram.fsm.state import State, StatesGroup


class CreativeStates(StatesGroup):
    """Состояния для процесса создания креатива"""
    
    # Выбор формы креатива
    select_form = State()
    
    # Загрузка медиа (для форм с медиа)
    upload_media = State()
    
    # Ввод текста (для форм с текстом)
    enter_text = State()
    
    # Ввод целевых ссылок (необязательно)
    enter_advertiser_urls = State()
    
    # Выбор кода ККТУ
    select_kktu = State()
    
    # Подтверждение создания
    confirm_creation = State()

