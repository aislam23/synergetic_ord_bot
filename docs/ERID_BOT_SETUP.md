# Настройка бота для создания токенов Erid

## Описание

Бот для создания креативов саморекламы и получения токенов Erid через API Медиаскаут.

## Возможности

- ✅ Создание креативов саморекламы через API Медиаскаут
- ✅ Поддержка всех форм креативов (Banner, Text, Video, Audio и т.д.)
- ✅ Загрузка медиа-файлов (фото, видео, аудио, документы)
- ✅ Ввод текстовых данных
- ✅ Выбор кодов ККТУ (категории товаров/услуг)
- ✅ Получение токена Erid
- ✅ Все кнопки реализованы как inline

## Параметры по умолчанию

Для всех креативов автоматически устанавливаются следующие параметры:

- `isSelfPromotion = true` (саморекламa)
- `type = Other` (тип кампании)
- `isCobranding = false`
- `isNative = false`
- `isSocial = false`
- `isSocialQuota = false`

## Настройка переменных окружения

Создайте файл `.env` на основе примера ниже:

```bash
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
BOT_USERNAME=your_bot_username

# Admin Users (JSON array or comma-separated)
ADMIN_USER_IDS=[123456789]

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=botdb
POSTGRES_USER=botuser
POSTGRES_PASSWORD=your_postgres_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Mediascout API Configuration
# Контур "препрод" (для тестов): https://demo.mediascout.ru/webapi
# Контур "прод" (боевой): https://lk.mediascout.ru/webapi
MEDIASCOUT_API_URL=https://demo.mediascout.ru/webapi
MEDIASCOUT_LOGIN=your_mediascout_login
MEDIASCOUT_PASSWORD=your_mediascout_password

# Environment
ENV=development

# Logging
LOG_LEVEL=INFO
```

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск бота

```bash
python -m app.main
```

## Процесс создания креатива

1. **Команда /start** - запуск бота и показ главного меню
2. **Команда /menu** - показ главного меню
3. **Создать креатив** - начало процесса создания
4. **Выбор формы креатива** - выбор из 14 доступных форм:
   - Banner - Баннер
   - Text - Текстовый блок
   - TextGraphic - Текстово-графический блок
   - Video - Видеоролик
   - Audio - Аудиозапись
   - AudioBroadcast - Аудиотрансляции в прямом эфире
   - VideoBroadcast - Видеотрансляции в прямом эфире
   - TextVideoBlock - Текстовый блок с видео
   - TextAudioBlock - Текстовый блок с аудио
   - TextAudioVideoBlock - Текстовый блок с аудио и видео
   - TextGraphicVideoBlock - Текстово-графический блок с видео
   - TextGraphicAudioBlock - Текстово-графический блок с аудио
   - TextGraphicAudioVideoBlock - Текстово-графический блок с аудио и видео
   - BannerHtml5 - HTML5-баннер

5. **Загрузка медиа** (если требуется для выбранной формы)
6. **Ввод текста** (если требуется для выбранной формы)
7. **Выбор кода ККТУ** - категория товара/услуги
8. **Подтверждение** - проверка данных и создание
9. **Получение токена Erid** - готовый токен для использования

## Формы креативов

### Формы с медиа-файлами:
- Banner, TextGraphic, Video, Audio, AudioBroadcast, VideoBroadcast
- TextVideoBlock, TextAudioBlock, TextAudioVideoBlock
- TextGraphicVideoBlock, TextGraphicAudioBlock, TextGraphicAudioVideoBlock
- BannerHtml5

### Формы с текстом:
- Text, TextGraphic, TextVideoBlock, TextAudioBlock, TextAudioVideoBlock
- TextGraphicVideoBlock, TextGraphicAudioBlock, TextGraphicAudioVideoBlock

## Коды ККТУ

Бот поддерживает выбор из более чем 40 категорий ККТУ 3 уровня, включая:

- Алкогольная и табачная продукция (1.x.x)
- Медицинские товары и услуги (2.x.x)
- Азартные игры и лотереи (3.x.x)
- Финансовые услуги (4.x.x)
- Товары и услуги общего назначения (30.x.x)

## API Endpoints

Используемые методы API Медиаскаут:

- `GET /webapi/ping` - проверка связи
- `GET /webapi/pingauth` - проверка авторизации
- `GET /webapi/v3/dictionaries/kktu` - получение кодов ККТУ
- `POST /webapi/v3/creatives` - создание креатива

## Структура проекта

```
app/
├── handlers/
│   ├── creative.py          # Обработчики для создания креативов
│   ├── start.py             # Команда /start
│   └── ...
├── keyboards/
│   └── creative.py          # Inline клавиатуры для креативов
├── services/
│   └── mediascout.py        # Сервис для работы с API Медиаскаут
├── states/
│   └── creative.py          # States для FSM процесса создания
├── database/
│   └── models.py            # Модель Creative для хранения креативов
└── config.py                # Конфигурация с настройками API
```

## Примечания

- Для саморекламы не требуются договоры (`finalContractId` и `initialContractId`)
- Все суммы равны нулю для саморекламы
- Медиа-файлы автоматически конвертируются в base64 для отправки в API
- Поддерживается пагинация при выборе кодов ККТУ

## Логирование

Все операции логируются с использованием `loguru`:
- Успешное создание креативов
- Ошибки API
- Ошибки загрузки файлов

## TODO

- [ ] Добавить сохранение креативов в базу данных
- [ ] Реализовать просмотр истории креативов пользователя
- [ ] Добавить экспорт списка креативов

