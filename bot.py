"""
ARCTURUS Bot - Полная рабочая версия
Всё в одном файле как твой локальный бот + Flask для Render
"""

import os
import sys
import logging
import threading
import time
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# ==================== ЛОГИРОВАНИЕ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '')
WEBAPP_URL = os.getenv('WEBAPP_URL', '')
RENDER_URL = os.getenv('RENDER_URL', '')
PORT = int(os.getenv('PORT', '10000'))
TRIGGER_HASHTAG = '#arcturus'

# Проверка переменных
if not all([BOT_TOKEN, ADMIN_ID, CHANNEL_USERNAME, WEBAPP_URL, RENDER_URL]):
    logger.error("❌ Не все переменные окружения установлены!")
    sys.exit(1)

logger.info("=" * 70)
logger.info("✅ КОНФИГУРАЦИЯ ЗАГРУЖЕНА")
logger.info(f"👤 Admin ID: {ADMIN_ID}")
logger.info(f"📢 Канал: {CHANNEL_USERNAME}")
logger.info(f"🌐 WebApp: {WEBAPP_URL}")
logger.info("=" * 70)

# ==================== БОТ ====================
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Временное хранилище для пересланных сообщений
forwarded_messages = {}

def is_admin(message):
    """Проверка админа"""
    return message.from_user.id == ADMIN_ID

def create_markup():
    """Создание кнопки с ссылкой на WebApp"""
    markup = InlineKeyboardMarkup()
    info_button = InlineKeyboardButton(
        text="📱 Открыть каталог",
        url=WEBAPP_URL  # ← ИСПРАВЛЕНО! Обычная URL вместо WebApp
    )
    markup.row(info_button)
    return markup

# ==================== HANDLERS ====================

@bot.message_handler(func=lambda message: not is_admin(message))
def handle_unauthorized(message):
    """Удаляем сообщения от не-админов"""
    logger.warning(f"⚠️ Неавторизованный доступ: {message.from_user.id}")
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

@bot.message_handler(commands=['start'])
def cmd_start(message):
    """Команда /start"""
    if not is_admin(message):
        return
    
    logger.info(f"🔔 /start от {message.from_user.username} (ID: {message.from_user.id})")
    
    text = (
        f"✅ <b>Привет, админ!</b>\n\n"
        f"📋 <b>Как публиковать:</b>\n"
        f"1. Отправь пост (текст/фото/видео)\n"
        f"2. Добавь хэштег <code>{TRIGGER_HASHTAG}</code>\n"
        f"3. Пост опубликуется с кнопкой WebApp!\n\n"
        f"📢 Канал: {CHANNEL_USERNAME}\n"
        f"🔑 Твой ID: <code>{message.from_user.id}</code>\n\n"
        f"<b>Команды:</b>\n"
        f"/start - Это сообщение\n"
        f"/status - Статус бота"
    )
    
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Команда /status"""
    if not is_admin(message):
        return
    
    try:
        bot.get_chat(CHANNEL_USERNAME)
        channel_status = "✅ Подключён"
    except Exception as e:
        channel_status = f"❌ {str(e)}"
    
    text = (
        f"🤖 <b>Статус бота</b>\n\n"
        f"<b>Канал:</b> {CHANNEL_USERNAME}\n"
        f"<b>Статус:</b> {channel_status}\n"
        f"<b>Триггер:</b> {TRIGGER_HASHTAG}\n"
        f"<b>Admin ID:</b> {ADMIN_ID}\n"
        f"<b>WebApp:</b> {WEBAPP_URL}\n\n"
        f"✅ Бот активен"
    )
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(content_types=[
    'text', 'photo', 'video', 'document', 
    'audio', 'voice', 'video_note', 'animation', 'sticker'
])
def handle_all_messages(message):
    """Обработка всех сообщений"""
    if not is_admin(message):
        return
    
    user_id = message.from_user.id
    
    # ==================== ПЕРЕСЛАННЫЕ СООБЩЕНИЯ ====================
    if message.forward_date or message.forward_from or message.forward_from_chat:
        logger.info(f"📨 Получено пересланное сообщение от {message.from_user.username}")
        
        # Инициализируем буфер
        if user_id not in forwarded_messages:
            forwarded_messages[user_id] = []
        
        # Добавляем в буфер
        forwarded_messages[user_id].append(message)
        
        # Удаляем из чата с ботом
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        
        # Запускаем обработку группы
        def process_forwarded_group():
            time.sleep(1)  # Ждём 1 секунду
            
            if user_id in forwarded_messages and forwarded_messages[user_id]:
                messages_to_send = forwarded_messages[user_id].copy()
                forwarded_messages[user_id] = []
                
                sent_message_ids = []
                
                try:
                    # Пересылаем все
                    for msg in messages_to_send:
                        sent_msg = bot.forward_message(
                            chat_id=CHANNEL_USERNAME,
                            from_chat_id=msg.chat.id,
                            message_id=msg.message_id
                        )
                        sent_message_ids.append(sent_msg.message_id)
                    
                    logger.info(f"✅ Переслано {len(sent_message_ids)} сообщений в канал")
                    
                    # Добавляем кнопку к последнему
                    if sent_message_ids:
                        last_msg_id = sent_message_ids[-1]
                        try:
                            bot.edit_message_reply_markup(
                                chat_id=CHANNEL_USERNAME,
                                message_id=last_msg_id,
                                reply_markup=create_markup()
                            )
                            logger.info("✅ Кнопка добавлена к последнему сообщению")
                        except Exception as e:
                            logger.warning(f"⚠️ Не удалось добавить кнопку: {e}")
                            # Отправляем отдельно
                            bot.send_message(
                                chat_id=CHANNEL_USERNAME,
                                text="👆 Смотрите выше",
                                reply_markup=create_markup()
                            )
                
                except Exception as e:
                    logger.error(f"❌ Ошибка пересылки: {e}")
        
        # Запускаем в отдельном потоке
        threading.Thread(target=process_forwarded_group, daemon=True).start()
    
    # ==================== ОБЫЧНЫЕ СООБЩЕНИЯ С ХЭШТЕГОМ ====================
    else:
        caption = message.caption if message.caption else ""
        text = message.text if message.text else ""
        full_text = (caption + text).lower()
        
        if TRIGGER_HASHTAG.lower() in full_text:
            logger.info(f"📤 Публикация поста с хэштегом {TRIGGER_HASHTAG}")
            
            try:
                # Копируем в канал
                sent_msg = bot.copy_message(
                    chat_id=CHANNEL_USERNAME,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    disable_notification=True
                )
                
                logger.info(f"✅ Пост скопирован в канал (ID: {sent_msg.message_id})")
                
                # Добавляем кнопку
                try:
                    bot.edit_message_reply_markup(
                        chat_id=CHANNEL_USERNAME,
                        message_id=sent_msg.message_id,
                        reply_markup=create_markup()
                    )
                    logger.info("✅ Кнопка добавлена к посту")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить кнопку: {e}")
                    # Отправляем отдельно
                    bot.send_message(
                        chat_id=CHANNEL_USERNAME,
                        text="👆 Смотрите пост выше",
                        reply_markup=create_markup()
                    )
                
                # Удаляем оригинал
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except:
                    pass
                
                # Уведомление
                success_msg = bot.send_message(
                    message.chat.id,
                    "✅ <b>Пост опубликован!</b>",
                    parse_mode='HTML'
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
                logger.error(f"❌ Ошибка публикации: {e}")
                bot.send_message(
                    message.chat.id,
                    f"❌ <b>Ошибка:</b> {str(e)}",
                    parse_mode='HTML'
                )

# ==================== FLASK ДЛЯ RENDER ====================
app = Flask(__name__)
webhook_count = 0

@app.route('/')
def index():
    """Главная страница"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ARCTURUS Bot</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .container {{
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 15px;
            }}
            h1 {{ margin: 0 0 20px 0; }}
            .status {{ color: #4ade80; font-weight: bold; font-size: 1.2em; }}
            .info {{
                background: rgba(255,255,255,0.05);
                padding: 15px;
                border-radius: 10px;
                margin: 15px 0;
            }}
            a {{ color: #60a5fa; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 ARCTURUS Bot</h1>
            <p class="status">✅ Бот работает</p>
            <div class="info">
                <p><strong>Канал:</strong> {CHANNEL_USERNAME}</p>
                <p><strong>Admin ID:</strong> {ADMIN_ID}</p>
                <p><strong>Webhook вызовов:</strong> {webhook_count}</p>
                <p><strong>WebApp:</strong> <a href="{WEBAPP_URL}" target="_blank">Открыть</a></p>
            </div>
            <p>
                <a href="/health">Health Check</a> | 
                <a href="/webhook_info">Webhook Info</a> | 
                <a href="/set_webhook">Set Webhook</a>
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check для UptimeRobot"""
    return jsonify({'status': 'ok', 'webhook_calls': webhook_count}), 200

@app.route('/webhook_info')
def webhook_info():
    """Информация о webhook"""
    try:
        info = bot.get_webhook_info()
        return jsonify({
            'url': info.url,
            'pending_updates': info.pending_update_count,
            'allowed_updates': info.allowed_updates,
            'last_error_date': info.last_error_date,
            'last_error_message': info.last_error_message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/set_webhook')
def set_webhook_route():
    """Установка webhook"""
    try:
        webhook_url = f"{RENDER_URL.rstrip('/')}/{BOT_TOKEN}"
        
        # Удаляем старый
        bot.remove_webhook()
        logger.info("🗑️ Старый webhook удалён")
        
        # Устанавливаем новый
        bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "channel_post"]
        )
        
        logger.info(f"✅ Webhook установлен: {webhook_url}")
        
        info = bot.get_webhook_info()
        
        return jsonify({
            'status': 'success',
            'webhook_url': webhook_url,
            'allowed_updates': info.allowed_updates
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Обработка webhook от Telegram"""
    global webhook_count
    webhook_count += 1
    
    try:
        if request.headers.get('content-type') != 'application/json':
            return 'Invalid content type', 403
        
        json_string = request.get_data().decode('utf-8')
        logger.info(f"📥 Webhook #{webhook_count}")
        
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        
        logger.info(f"✅ Update #{webhook_count} обработан")
        return '', 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}")
        import traceback
        traceback.print_exc()
        return '', 500

# ==================== STARTUP ====================
@app.before_request
def setup_webhook_once():
    """Автоматическая установка webhook"""
    if not hasattr(app, 'webhook_initialized'):
        try:
            webhook_url = f"{RENDER_URL.rstrip('/')}/{BOT_TOKEN}"
            
            logger.info("=" * 70)
            logger.info("🔄 УСТАНОВКА WEBHOOK...")
            logger.info("=" * 70)
            
            bot.remove_webhook()
            logger.info("🗑️ Старый webhook удалён")
            
            bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "channel_post"]
            )
            
            logger.info(f"✅ Webhook: {webhook_url}")
            logger.info(f"📋 Allowed: message, channel_post")
            
            app.webhook_initialized = True
            
            logger.info("=" * 70)
            logger.info("✅ WEBHOOK ГОТОВ!")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"❌ Ошибка webhook: {e}")

# ==================== MAIN ====================
if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("🚀 ЗАПУСК ARCTURUS BOT")
    logger.info("=" * 70)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)