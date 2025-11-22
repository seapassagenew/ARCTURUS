"""
Обработчики сообщений с максимальной безопасностью
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
    
    # КРИТИЧЕСКАЯ ПРОВЕРКА БЕЗОПАСНОСТИ
    def security_check(message: telebot.types.Message) -> bool:
        """Жёсткая проверка доступа"""
        user_id = message.from_user.id
        username = message.from_user.username or "NO_USERNAME"
        
        if not is_admin(user_id):
            log_action("🚫 UNAUTHORIZED", user_id, username)
            
            # Удаляем сообщение злоумышленника
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            
            # Отправляем предупреждение
            warning = bot.send_message(
                message.chat.id,
                f"🚫 <b>ДОСТУП ЗАПРЕЩЁН</b>\n\n"
                f"ID: <code>{user_id}</code>\n"
                f"Username: @{username}\n\n"
                f"Этот инцидент зафиксирован.",
                parse_mode='HTML'
            )
            
            # Удаляем предупреждение через 10 секунд
            import time
            import threading
            def delete_warning():
                time.sleep(10)
                try:
                    bot.delete_message(warning.chat.id, warning.message_id)
                except:
                    pass
            threading.Thread(target=delete_warning, daemon=True).start()
            
            return False
        
        return True
    
    
    @bot.message_handler(commands=['start'])
    def start_command(message: telebot.types.Message):
        """Команда /start"""
        if not security_check(message):
            return
        
        user_id = message.from_user.id
        username = message.from_user.username or "NO_USERNAME"
        
        log_action("✅ START", user_id, username)
        
        response = (
            "🤖 <b>ARCTURUS Bot активен</b>\n\n"
            "📋 <b>Инструкция:</b>\n\n"
            "1. Отправь пост (текст/фото/видео/документ)\n"
            f"2. Добавь хэштег <code>{Config.TRIGGER_HASHTAG}</code>\n"
            "3. Пост автоматически опубликуется с кнопкой WebApp!\n\n"
            "💡 <b>Пример:</b>\n"
            f"<i>Новый пост! {Config.TRIGGER_HASHTAG}</i>\n\n"
            "⚙️ <b>Команды:</b>\n"
            "/start - Показать инструкцию\n"
            "/status - Статус бота\n"
            "/test - Тестовая публикация\n\n"
            f"🆔 Ваш ID: <code>{user_id}</code>"
        )
        
        bot.send_message(
            message.chat.id,
            response,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    
    
    @bot.message_handler(commands=['status'])
    def status_command(message: telebot.types.Message):
        """Статус бота"""
        if not security_check(message):
            return
        
        user_id = message.from_user.id
        username = message.from_user.username or "NO_USERNAME"
        
        log_action("📊 STATUS", user_id, username)
        
        # Проверка канала
        try:
            chat = bot.get_chat(Config.CHANNEL_USERNAME)
            channel_status = f"✅ Подключён\nТип: {chat.type}"
        except Exception as e:
            channel_status = f"❌ Ошибка: {str(e)}"
        
        # Проверка webhook
        try:
            webhook_info = bot.get_webhook_info()
            webhook_status = f"✅ Активен\nURL: {webhook_info.url[:50]}..."
        except:
            webhook_status = "❌ Не установлен"
        
        response = (
            "📊 <b>СТАТУС БОТА</b>\n\n"
            f"<b>Канал:</b> {Config.CHANNEL_USERNAME}\n"
            f"{channel_status}\n\n"
            f"<b>Webhook:</b>\n{webhook_status}\n\n"
            f"<b>Триггер:</b> <code>{Config.TRIGGER_HASHTAG}</code>\n"
            f"<b>Админов:</b> {len(Config.ADMIN_IDS)}\n"
            f"<b>WebApp:</b> {Config.WEBAPP_URL}\n\n"
            "✅ Бот работает"
        )
        
        bot.send_message(
            message.chat.id,
            response,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    
    
    @bot.message_handler(commands=['test'])
    def test_command(message: telebot.types.Message):
        """Тестовая публикация"""
        if not security_check(message):
            return
        
        user_id = message.from_user.id
        username = message.from_user.username or "NO_USERNAME"
        
        log_action("🧪 TEST", user_id, username)
        
        try:
            # Отправляем тестовый пост
            test_msg = bot.send_message(
                Config.CHANNEL_USERNAME,
                f"🧪 Тестовый пост\n\nОтправлено ботом ARCTURUS\n{Config.TRIGGER_HASHTAG}",
                reply_markup=create_webapp_button()
            )
            
            bot.send_message(
                message.chat.id,
                f"✅ Тест успешен!\n\n"
                f"Пост опубликован в {Config.CHANNEL_USERNAME}\n"
                f"ID сообщения: {test_msg.message_id}",
                parse_mode='HTML'
            )
            
        except Exception as e:
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка теста:\n\n{format_error_message(e)}",
                parse_mode='HTML'
            )
    
    
    @bot.message_handler(content_types=[
        'text', 'photo', 'video', 'document', 
        'audio', 'voice', 'video_note', 'animation'
    ])
    def handle_content(message: telebot.types.Message):
        """Обработка всех типов контента"""
        
        # ПЕРВАЯ ПРОВЕРКА - безопасность
        if not security_check(message):
            return
        
        user_id = message.from_user.id
        username = message.from_user.username or "NO_USERNAME"
        
        # Извлекаем текст
        text = extract_text_from_message(message)
        
        # ВТОРАЯ ПРОВЕРКА - наличие триггера
        if not has_trigger_hashtag(text):
            # Сообщение без триггера игнорируем
            return
        
        log_action("📤 PUBLISH_START", user_id, username, f"Type: {message.content_type}")
        
        try:
            # Копируем сообщение в канал
            sent_message = bot.copy_message(
                chat_id=Config.CHANNEL_USERNAME,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            
            log_action("✅ COPIED", user_id, username, f"Msg ID: {sent_message.message_id}")
            
            # Добавляем кнопку
            try:
                bot.edit_message_reply_markup(
                    chat_id=Config.CHANNEL_USERNAME,
                    message_id=sent_message.message_id,
                    reply_markup=create_webapp_button()
                )
                log_action("✅ BUTTON_ADDED", user_id, username)
                
            except Exception as btn_error:
                # Если не получилось прикрепить кнопку к сообщению
                log_action("⚠️ BUTTON_FAILED", user_id, username, str(btn_error))
                
                # Отправляем кнопку отдельным сообщением
                bot.send_message(
                    chat_id=Config.CHANNEL_USERNAME,
                    text="👆 Смотри пост выше",
                    reply_markup=create_webapp_button()
                )
            
            # Удаляем оригинал из чата с ботом
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            
            # Уведомление об успехе
            success_msg = bot.send_message(
                message.chat.id,
                f"✅ <b>Опубликовано!</b>\n\n"
                f"📢 {Config.CHANNEL_USERNAME}\n"
                f"🔘 WebApp добавлен\n"
                f"🆔 ID поста: {sent_message.message_id}",
                parse_mode='HTML'
            )
            
            # Удаляем уведомление через 8 секунд
            import time
            import threading
            def delete_notification():
                time.sleep(8)
                try:
                    bot.delete_message(success_msg.chat.id, success_msg.message_id)
                except:
                    pass
            threading.Thread(target=delete_notification, daemon=True).start()
            
            log_action("✅ PUBLISH_SUCCESS", user_id, username)
            
        except Exception as e:
            error_msg = format_error_message(e)
            log_action("❌ PUBLISH_ERROR", user_id, username, error_msg)
            
            bot.send_message(
                message.chat.id,
                f"❌ <b>Ошибка публикации</b>\n\n{error_msg}",
                parse_mode='HTML'
            )
    
    
    # Обработчик для всех остальных типов сообщений
    @bot.message_handler(content_types=['sticker', 'location', 'contact', 'poll'])
    def handle_other(message: telebot.types.Message):
        """Обработка неподдерживаемых типов"""
        if not security_check(message):
            return
        
        bot.send_message(
            message.chat.id,
            "⚠️ Этот тип контента не поддерживается для публикации"
        )