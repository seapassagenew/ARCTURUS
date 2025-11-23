"""
Вспомогательные функции - УПРОЩЕНО
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import Config


def is_admin(user_id: int) -> bool:
    """Проверка админа - СТРОГАЯ"""
    return user_id == Config.ADMIN_ID


def create_webapp_button(text: str = "📱 Открыть каталог") -> InlineKeyboardMarkup:
    """Создание кнопки с WebApp"""
    markup = InlineKeyboardMarkup()
    webapp_button = InlineKeyboardButton(
        text=text,
        web_app=WebAppInfo(url=Config.WEBAPP_URL)
    )
    markup.add(webapp_button)
    return markup


def extract_text_from_message(message: telebot.types.Message) -> str:
    """Извлечение текста из сообщения"""
    if message.caption:
        return message.caption
    elif message.text:
        return message.text
    return ""


def has_trigger_hashtag(text: str) -> bool:
    """Проверка хэштега"""
    if not text:
        return False
    return Config.TRIGGER_HASHTAG.lower() in text.lower()