"""
ARCTURUS Bot - Безопасная версия для Render
✅ Токен защищён секретным путём webhook
✅ Поддержка нескольких админов
✅ Полная защита от утечек данных в логах
"""

import os
import sys
import logging
import threading
import time
import secrets
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== БЕЗОПАСНОЕ ЛОГИРОВАНИЕ ====================
class SecureFormatter(logging.Formatter):
    """Кастомный форматтер, который скрывает чувствительные данные"""
    sensitive_data = []
    
    def format(self, record):
        original = super().format(record)
        result = original
        for secret in self.sensitive_data:
            if secret and len(str(secret)) > 5:
                result = result.replace(str(secret), '***HIDDEN***')
        return result

handler = logging.StreamHandler(sys.stdout)
secure_formatter = SecureFormatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(secure_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Отключаем логи библиотек
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('telebot').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# 🔥 ПОДДЕРЖКА НЕСКОЛЬКИХ АДМИНОВ через запятую
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = []

if ADMIN_IDS_STR:
    try:
        ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip()]
        if not ADMIN_IDS:
            raise ValueError("Список админов пуст")
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга ADMIN_IDS: {e}")
        logger.error(f"Формат должен быть: 123456789,987654321")
        sys.exit(1)
else:
    logger.error("❌ ADMIN_IDS не установлен!")
    sys.exit(1)

CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '')
WEBAPP_URL = os.getenv('WEBAPP_URL', '')
RENDER_URL = os.getenv('RENDER_URL', '')
PORT = int(os.getenv('PORT', '10000'))
TRIGGER_HASHTAG = '#arcturus'

# 🔒 Секретный ключ для доступа к служебным эндпоинтам
ADMIN_SECRET = os.getenv('ADMIN_SECRET', '')
if not ADMIN_SECRET:
    logger.warning("⚠️ ADMIN_SECRET не установлен! Генерирую случайный...")
    ADMIN_SECRET = secrets.token_urlsafe(32)
    logger.info(f"🔑 Сгенерированный ключ (сохрани!): {ADMIN_SECRET}")

# 🔥 СЕКРЕТНЫЙ ПУТЬ для webhook (вместо токена!)
WEBHOOK_SECRET_PATH = os.getenv('WEBHOOK_SECRET_PATH', '')
if not WEBHOOK_SECRET_PATH:
    logger.warning("⚠️ WEBHOOK_SECRET_PATH не установлен! Генерирую случайный...")
    WEBHOOK_SECRET_PATH = secrets.token_urlsafe(32)
    logger.info(f"🔑 Сгенерированный путь (сохрани!): {WEBHOOK_SECRET_PATH}")

# Добавляем все секреты в список для скрытия в логах
SecureFormatter.sensitive_data = [
    BOT_TOKEN,
    ADMIN_SECRET,
    WEBHOOK_SECRET_PATH,
    *[str(id) for id in ADMIN_IDS]
]

# Проверка переменных
if not all([BOT_TOKEN, CHANNEL_USERNAME, WEBAPP_URL, RENDER_URL]):
    logger.error("❌ Не все переменные окружения установлены!")
    sys.exit(1)

logger.info("=" * 70)
logger.info("✅ КОНФИГУРАЦИЯ ЗАГРУЖЕНА")
logger.info(f"📢 Канал: {CHANNEL_USERNAME}")
logger.info(f"🌐 WebApp: {WEBAPP_URL}")
logger.info(f"👥 Количество админов: {len(ADMIN_IDS)}")
logger.info(f"🔐 Секретный ключ: ✅ установлен")
logger.info(f"🔐 Webhook путь: ✅ защищён")
logger.info("=" * 70)

# ==================== БОТ ====================
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Временное хранилище для пересланных сообщений
forwarded_messages = {}

def is_admin(message):
    """Проверка админа (поддержка нескольких админов)"""
    return message.from_user.id in ADMIN_IDS

def create_markup():
    """Создание кнопки с ссылкой на WebApp"""
    markup = InlineKeyboardMarkup()
    info_button = InlineKeyboardButton(
        text="📱 Открыть каталог",
        url=WEBAPP_URL
    )
    markup.row(info_button)
    return markup

def safe_log_message(message, action):
    """Безопасное логирование без персональных данных"""
    return f"{action} от {'админ' if is_admin(message) else 'неавторизованный пользователь'}"

# ==================== HANDLERS ====================

@bot.message_handler(func=lambda message: not is_admin(message))
def handle_unauthorized(message):
    """Удаляем сообщения от не-админов"""
    logger.warning("⚠️ Попытка неавторизованного доступа (детали скрыты)")
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

@bot.message_handler(commands=['start'])
def cmd_start(message):
    """Команда /start"""
    if not is_admin(message):
        return
    
    logger.info(safe_log_message(message, "🔔 /start"))
    
    text = (
        f"✅ <b>Привет, админ!</b>\n\n"
        f"📋 <b>Как публиковать:</b>\n"
        f"1. Отправь пост (текст/фото/видео)\n"
        f"2. Добавь хэштег <code>{TRIGGER_HASHTAG}</code>\n"
        f"3. Пост опубликуется с кнопкой WebApp!\n\n"
        f"📢 Канал: {CHANNEL_USERNAME}\n"
        f"👥 Админов: {len(ADMIN_IDS)}\n\n"
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
        channel_status = f"❌ Ошибка подключения"
        logger.error("Ошибка проверки канала")
    
    text = (
        f"🤖 <b>Статус бота</b>\n\n"
        f"<b>Канал:</b> {CHANNEL_USERNAME}\n"
        f"<b>Статус:</b> {channel_status}\n"
        f"<b>Триггер:</b> {TRIGGER_HASHTAG}\n"
        f"<b>WebApp:</b> {WEBAPP_URL}\n"
        f"<b>Админов:</b> {len(ADMIN_IDS)}\n\n"
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
        logger.info(safe_log_message(message, "📨 Получено пересланное сообщение"))
        
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
                            logger.warning("⚠️ Не удалось добавить кнопку, отправляю отдельно")
                            # Отправляем отдельно
                            bot.send_message(
                                chat_id=CHANNEL_USERNAME,
                                text="👆 Смотрите выше",
                                reply_markup=create_markup()
                            )
                
                except Exception as e:
                    logger.error("❌ Ошибка пересылки сообщений")
        
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
                
                logger.info("✅ Пост скопирован в канал")
                
                # Добавляем кнопку
                try:
                    bot.edit_message_reply_markup(
                        chat_id=CHANNEL_USERNAME,
                        message_id=sent_msg.message_id,
                        reply_markup=create_markup()
                    )
                    logger.info("✅ Кнопка добавлена к посту")
                except Exception as e:
                    logger.warning("⚠️ Не удалось добавить кнопку, отправляю отдельно")
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
                logger.error("❌ Ошибка публикации поста")
                bot.send_message(
                    message.chat.id,
                    f"❌ <b>Ошибка публикации</b>\nПопробуйте ещё раз",
                    parse_mode='HTML'
                )

# ==================== FLASK ДЛЯ RENDER ====================
app = Flask(__name__)
webhook_count = 0

def check_admin_access():
    """Проверка доступа к служебным эндпоинтам"""
    secret = request.args.get('secret')
    if secret != ADMIN_SECRET:
        logger.warning("⚠️ Попытка несанкционированного доступа к служебному эндпоинту")
        return False
    return True

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
                <p><strong>WebApp:</strong> <a href="{WEBAPP_URL}" target="_blank">Открыть</a></p>
                <p><strong>Админов:</strong> {len(ADMIN_IDS)}</p>
                <p><strong>Webhook вызовов:</strong> {webhook_count}</p>
            </div>
            <p>
                <a href="/health">Health Check</a>
            </p>
            <p style="font-size: 0.9em; opacity: 0.7; margin-top: 20px;">
                🔒 Служебные эндпоинты защищены<br>
                🛡️ Webhook использует секретный путь
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check для UptimeRobot"""
    return jsonify({
        'status': 'ok', 
        'webhook_calls': webhook_count,
        'service': 'arcturus',
        'admins': len(ADMIN_IDS)
    }), 200

@app.route('/webhook_info')
def webhook_info():
    """Информация о webhook - ЗАЩИЩЕНО!"""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        info = bot.get_webhook_info()
        
        return jsonify({
            'url': '***HIDDEN***',
            'pending_updates': info.pending_update_count,
            'allowed_updates': info.allowed_updates,
            'last_error_date': info.last_error_date,
            'last_error_message': info.last_error_message if info.last_error_message else None,
            'uses_secret_path': True
        })
    except Exception as e:
        logger.error("❌ Ошибка получения информации о webhook")
        return jsonify({'error': 'Internal error'}), 500

@app.route('/set_webhook')
def set_webhook_route():
    """Установка webhook - ЗАЩИЩЕНО!"""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # 🔥 Используем секретный путь вместо токена!
        webhook_url = f"{RENDER_URL.rstrip('/')}/webhook/{WEBHOOK_SECRET_PATH}"
        
        # Удаляем старый
        bot.remove_webhook()
        logger.info("🗑️ Старый webhook удалён")
        
        # Устанавливаем новый
        bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "channel_post"]
        )
        
        logger.info("✅ Webhook установлен с секретным путём")
        
        info = bot.get_webhook_info()
        
        return jsonify({
            'status': 'success',
            'webhook_url': '***HIDDEN***',
            'allowed_updates': info.allowed_updates,
            'uses_secret_path': True
        })
        
    except Exception as e:
        logger.error("❌ Ошибка установки webhook")
        return jsonify({'error': 'Internal error'}), 500

# 🔥 БЕЗОПАСНЫЙ WEBHOOK с секретным путём
@app.route(f'/webhook/{WEBHOOK_SECRET_PATH}', methods=['POST'])
def webhook():
    """Обработка webhook от Telegram (ЗАЩИЩЁННЫЙ ПУТЬ)"""
    global webhook_count
    webhook_count += 1
    
    try:
        if request.headers.get('content-type') != 'application/json':
            logger.warning("⚠️ Неверный content-type webhook запроса")
            return 'Invalid content type', 403
        
        json_string = request.get_data().decode('utf-8')
        logger.info(f"📥 Webhook #{webhook_count}")
        
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        
        logger.info(f"✅ Update #{webhook_count} обработан")
        return '', 200
        
    except Exception as e:
        logger.error("❌ Ошибка обработки webhook")
        return '', 500

# ==================== STARTUP ====================
@app.before_request
def setup_webhook_once():
    """Автоматическая установка webhook"""
    if not hasattr(app, 'webhook_initialized'):
        try:
            # 🔥 Используем секретный путь вместо токена!
            webhook_url = f"{RENDER_URL.rstrip('/')}/webhook/{WEBHOOK_SECRET_PATH}"
            
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
            
            logger.info("✅ Webhook установлен с секретным путём")
            logger.info("📋 Allowed: message, channel_post")
            
            app.webhook_initialized = True
            
            logger.info("=" * 70)
            logger.info("✅ WEBHOOK ГОТОВ!")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error("❌ Ошибка установки webhook")

# ==================== MAIN ====================
if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("🚀 ЗАПУСК ARCTURUS BOT")
    logger.info("=" * 70)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)