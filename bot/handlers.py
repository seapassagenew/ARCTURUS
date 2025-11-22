"""
Обработчики сообщений для Telegram бота
"""

import telebot
from bot.config import Config
from bot.utils import (
    is_admin, 
    create_webapp_button, 
    extract_text_from_message,
    has_trigger_hashtag,
    format_error_message,
    log_action
)


def register_handlers(bot: telebot.TeleBot):
    """Регистрация всех обработчиков"""
    
    @bot.message_handler(commands=['start'])
    def start_command(message: telebot.types.Message):
        """Обработчик команды /start"""
        user_id = message.from_user.id
        username = message.from_user.username
        
        log_action("START", user_id, username)
        
        if is_admin(user_id):
            response = (
                "👋 <b>Привет, админ!</b>\n\n"
                "📋 <b>Как опубликовать пост с кнопкой:</b>\n\n"
                "1️⃣ Отправь мне пост (текст, фото, видео, документ)\n"
                f"2️⃣ Добавь хэштег <code>{Config.TRIGGER_HASHTAG}</code> в текст или подпись\n"
                "3️⃣ Пост автоматически опубликуется в канале с кнопкой WebApp!\n\n"
                "💡 <b>Примеры:</b>\n"
                f"• Текст поста {Config.TRIGGER_HASHTAG}\n"
                f"• Фото с подписью: Смотрите каталог! {Config.TRIGGER_HASHTAG}\n\n"
                "⚙️ <b>Команды:</b>\n"
                "/start - Это сообщение\n"
                "/help - Справка\n"
                "/status - Статус бота"
            )
        else:
            response = (
                "❌ <b>Доступ запрещён</b>\n\n"
                "У вас нет прав для использования этого бота.\n"
                f"Ваш ID: <code>{user_id}</code>"
            )
        
        bot.send_message(
            message.chat.id,
            response,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    
    
    @bot.message_handler(commands=['help'])
    def help_command(message: telebot.types.Message):
        """Обработчик команды /help"""
        user_id = message.from_user.id
        
        if not is_admin(user_id):
            bot.send_message(
                message.chat.id,
                "❌ У вас нет доступа к боту"
            )
            return
        
        response = (
            "📖 <b>Справка по использованию бота</b>\n\n"
            f"<b>Триггер публикации:</b> {Config.TRIGGER_HASHTAG}\n\n"
            "<b>Поддерживаемые типы контента:</b>\n"
            "• 📝 Текстовые сообщения\n"
            "• 🖼 Фотографии\n"
            "• 🎥 Видео\n"
            "• 📄 Документы\n"
            "• 🎵 Аудио\n"
            "• 🎤 Голосовые сообщения\n"
            "• 🎬 Видео-сообщения\n"
            "• 🎭 GIF анимации\n\n"
            "<b>Процесс публикации:</b>\n"
            "1. Бот копирует ваше сообщение в канал\n"
            "2. Добавляет кнопку с WebApp\n"
            "3. Удаляет оригинал из чата с ботом\n"
            "4. Отправляет уведомление об успехе\n\n"
            f"<b>Канал публикации:</b> {Config.CHANNEL_USERNAME}"
        )
        
        bot.send_message(
            message.chat.id,
            response,
            parse_mode='HTML'
        )
    
    
    @bot.message_handler(commands=['status'])
    def status_command(message: telebot.types.Message):
        """Обработчик команды /status"""
        user_id = message.from_user.id
        
        if not is_admin(user_id):
            bot.send_message(
                message.chat.id,
                "❌ У вас нет доступа к боту"
            )
            return
        
        # Проверка подключения к каналу
        try:
            bot.get_chat(Config.CHANNEL_USERNAME)
            channel_status = "✅ Подключён"
        except Exception as e:
            channel_status = f"❌ Ошибка: {str(e)}"
        
        response = (
            "🤖 <b>Статус бота</b>\n\n"
            f"<b>Версия:</b> 1.0.0\n"
            f"<b>Канал:</b> {Config.CHANNEL_USERNAME}\n"
            f"<b>Статус канала:</b> {channel_status}\n"
            f"<b>Триггер:</b> {Config.TRIGGER_HASHTAG}\n"
            f"<b>Админов:</b> {len(Config.ADMIN_IDS)}\n"
            f"<b>WebApp URL:</b> {Config.WEBAPP_URL}\n\n"
            "✅ Бот работает нормально"
        )
        
        bot.send_message(
            message.chat.id,
            response,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    
    
    @bot.message_handler(content_types=[
        'text', 'photo', 'video', 'document', 
        'audio', 'voice', 'video_note', 'animation', 'sticker'
    ])
    def handle_content(message: telebot.types.Message):
        """Обработчик всех типов контента"""
        user_id = message.from_user.id
        username = message.from_user.username
        
        # Проверка прав доступа
        if not is_admin(user_id):
            log_action("UNAUTHORIZED_ACCESS", user_id, username)
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            
            bot.send_message(
                message.chat.id,
                "❌ У вас нет прав для публикации в канале"
            )
            return
        
        # Извлечение текста
        text = extract_text_from_message(message)
        
        # Проверка наличия триггерного хэштега
        if not has_trigger_hashtag(text):
            # Не обрабатываем сообщения без хэштега
            return
        
        log_action("PUBLISH_ATTEMPT", user_id, username, f"Type: {message.content_type}")
        
        try:
            # Копируем сообщение в канал
            sent_message = bot.copy_message(
                chat_id=Config.CHANNEL_USERNAME,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            
            log_action("MESSAGE_COPIED", user_id, username, f"Message ID: {sent_message.message_id}")
            
            # Добавляем кнопку с WebApp
            try:
                bot.edit_message_reply_markup(
                    chat_id=Config.CHANNEL_USERNAME,
                    message_id=sent_message.message_id,
                    reply_markup=create_webapp_button()
                )
                log_action("BUTTON_ADDED", user_id, username)
            except Exception as e:
                # Если не удалось добавить кнопку к сообщению, отправляем отдельно
                log_action("BUTTON_ADD_FAILED", user_id, username, str(e))
                bot.send_message(
                    chat_id=Config.CHANNEL_USERNAME,
                    text="👆 Смотрите пост выше",
                    reply_markup=create_webapp_button()
                )
            
            # Удаляем оригинальное сообщение из чата с ботом
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            
            # Отправляем уведомление об успехе
            success_msg = bot.send_message(
                message.chat.id,
                "✅ <b>Пост опубликован!</b>\n\n"
                f"📢 Канал: {Config.CHANNEL_USERNAME}\n"
                "🔘 Кнопка WebApp добавлена",
                parse_mode='HTML',
                disable_notification=True
            )
            
            # Удаляем уведомление через 5 секунд
            import time
            import threading
            
            def delete_notification():
                time.sleep(5)
                try:
                    bot.delete_message(success_msg.chat.id, success_msg.message_id)
                except:
                    pass
            
            threading.Thread(target=delete_notification, daemon=True).start()
            
            log_action("PUBLISH_SUCCESS", user_id, username)
            
        except Exception as e:
            error_msg = format_error_message(e)
            log_action("PUBLISH_ERROR", user_id, username, error_msg)
            
            bot.send_message(
                message.chat.id,
                f"❌ <b>Ошибка публикации</b>\n\n{error_msg}",
                parse_mode='HTML'
            )