"""
Обработчики сообщений - ИСПРАВЛЕНО
"""

import telebot
import time
import threading
from bot.config import Config
from bot.utils import (
    is_admin, 
    create_webapp_button, 
    extract_text_from_message,
    has_trigger_hashtag
)


def register_handlers(bot: telebot.TeleBot):
    """Регистрация всех обработчиков"""
    
    @bot.message_handler(commands=['start'])
    def start_command(message: telebot.types.Message):
        """Команда /start"""
        user_id = message.from_user.id
        username = message.from_user.username or "Без username"
        
        print(f"🔔 /start от {username} (ID: {user_id})")
        
        if is_admin(user_id):
            response = (
                f"✅ <b>Привет, админ!</b>\n\n"
                f"📋 <b>Как публиковать:</b>\n"
                f"1. Отправь пост (текст/фото/видео)\n"
                f"2. Добавь хэштег <code>{Config.TRIGGER_HASHTAG}</code>\n"
                f"3. Пост опубликуется с кнопкой WebApp\n\n"
                f"📢 Канал: {Config.CHANNEL_USERNAME}\n"
                f"🔑 Ваш ID: <code>{user_id}</code>"
            )
        else:
            response = (
                f"❌ <b>Доступ запрещён</b>\n\n"
                f"Ваш ID: <code>{user_id}</code>\n"
                f"Вы не являетесь администратором этого бота."
            )
        
        bot.send_message(
            message.chat.id,
            response,
            parse_mode='HTML'
        )
    
    
    @bot.message_handler(commands=['status'])
    def status_command(message: telebot.types.Message):
        """Статус бота"""
        user_id = message.from_user.id
        
        if not is_admin(user_id):
            bot.send_message(message.chat.id, "❌ Доступ запрещён")
            return
        
        try:
            bot.get_chat(Config.CHANNEL_USERNAME)
            channel_status = "✅ Подключён"
        except Exception as e:
            channel_status = f"❌ {str(e)}"
        
        response = (
            f"🤖 <b>Статус бота</b>\n\n"
            f"<b>Канал:</b> {Config.CHANNEL_USERNAME}\n"
            f"<b>Статус:</b> {channel_status}\n"
            f"<b>Триггер:</b> {Config.TRIGGER_HASHTAG}\n"
            f"<b>Admin ID:</b> {Config.ADMIN_ID}\n"
            f"<b>WebApp:</b> {Config.WEBAPP_URL}\n\n"
            f"✅ Бот активен"
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
        """Обработчик контента"""
        user_id = message.from_user.id
        username = message.from_user.username or "Без username"
        
        # СТРОГАЯ ПРОВЕРКА АДМИНА
        if not is_admin(user_id):
            print(f"⚠️ Неавторизованный доступ: {username} (ID: {user_id})")
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            return
        
        # Извлекаем текст
        text = extract_text_from_message(message)
        
        # Проверяем хэштег
        if not has_trigger_hashtag(text):
            return
        
        print(f"📤 Публикация от {username} | Тип: {message.content_type}")
        
        try:
            # Копируем сообщение в канал
            sent_message = bot.copy_message(
                chat_id=Config.CHANNEL_USERNAME,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            
            print(f"✅ Сообщение скопировано (ID: {sent_message.message_id})")
            
            # Добавляем кнопку
            try:
                bot.edit_message_reply_markup(
                    chat_id=Config.CHANNEL_USERNAME,
                    message_id=sent_message.message_id,
                    reply_markup=create_webapp_button()
                )
                print("✅ Кнопка добавлена")
            except Exception as e:
                print(f"⚠️ Не удалось добавить кнопку: {e}")
                # Отправляем отдельно
                bot.send_message(
                    chat_id=Config.CHANNEL_USERNAME,
                    text="👆 Смотрите пост выше",
                    reply_markup=create_webapp_button()
                )
            
            # Удаляем оригинал
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            
            # Уведомление
            success_msg = bot.send_message(
                message.chat.id,
                "✅ <b>Опубликовано!</b>",
                parse_mode='HTML',
                disable_notification=True
            )
            
            # Удаляем уведомление через 3 секунды
            def delete_notification():
                time.sleep(3)
                try:
                    bot.delete_message(success_msg.chat.id, success_msg.message_id)
                except:
                    pass
            
            threading.Thread(target=delete_notification, daemon=True).start()
            
        except Exception as e:
            print(f"❌ Ошибка публикации: {e}")
            bot.send_message(
                message.chat.id,
                f"❌ <b>Ошибка:</b> {str(e)}",
                parse_mode='HTML'
            )