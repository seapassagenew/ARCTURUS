"""
Вспомогательные функции для бота
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import Config


def is_admin(user_id: int) -> bool:
    """
    Проверка, является ли пользователь администратором
    
    Args:
        user_id: Telegram ID пользователя
    
    Returns:
        True если пользователь админ, иначе False
    """
    return user_id in Config.ADMIN_IDS


def create_webapp_button(text: str = "📱 Открыть каталог") -> InlineKeyboardMarkup:
    """
    Создание кнопки с WebApp
    
    Args:
        text: Текст на кнопке
    
    Returns:
        InlineKeyboardMarkup с кнопкой WebApp
    """
    markup = InlineKeyboardMarkup()
    webapp_button = InlineKeyboardButton(
        text=text,
        web_app=WebAppInfo(url=Config.WEBAPP_URL)
    )
    markup.add(webapp_button)
    return markup


def extract_text_from_message(message: telebot.types.Message) -> str:
    """
    Извлечение текста из сообщения (текст или подпись)
    
    Args:
        message: Объект сообщения Telegram
    
    Returns:
        Текст сообщения или пустая строка
    """
    if message.caption:
        return message.caption
    elif message.text:
        return message.text
    return ""


def has_trigger_hashtag(text: str) -> bool:
    """
    Проверка наличия триггерного хэштега в тексте
    
    Args:
        text: Текст для проверки
    
    Returns:
        True если хэштег найден, иначе False
    """
    return Config.TRIGGER_HASHTAG.lower() in text.lower()


def format_error_message(error: Exception) -> str:
    """
    Форматирование сообщения об ошибке
    
    Args:
        error: Объект исключения
    
    Returns:
        Отформатированное сообщение об ошибке
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Специальная обработка для частых ошибок
    if "chat not found" in error_message.lower():
        return "❌ Канал не найден. Проверьте CHANNEL_USERNAME"
    elif "forbidden" in error_message.lower():
        return "❌ Бот не является админом канала"
    elif "message can't be edited" in error_message.lower():
        return "❌ Не удалось добавить кнопку (сообщение нельзя редактировать)"
    
    return f"❌ Ошибка ({error_type}): {error_message}"


def log_action(action: str, user_id: int, username: str = None, details: str = ""):
    """
    Логирование действий пользователей
    
    Args:
        action: Описание действия
        user_id: ID пользователя
        username: Username пользователя (опционально)
        details: Дополнительные детали (опционально)
    """
    user_info = f"@{username}" if username else f"ID:{user_id}"
    log_message = f"[{action}] {user_info}"
    if details:
        log_message += f" | {details}"
    print(log_message)