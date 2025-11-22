"""
Flask приложение для Telegram бота - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

import os
import telebot
from flask import Flask, request, jsonify
from datetime import datetime

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME', '')
WEBAPP_URL = os.environ.get('WEBAPP_URL', '')
ADMIN_IDS = [int(id.strip()) for id in os.environ.get('ADMIN_IDS', '').split(',') if id.strip()]
RENDER_URL = os.environ.get('RENDER_URL', '')
TRIGGER_HASHTAG = '#arcturus'

# Проверка
if not all([BOT_TOKEN, CHANNEL_USERNAME, WEBAPP_URL, RENDER_URL]):
    print("❌ ОШИБКА: Не все переменные окружения заданы!")
    exit(1)

print(f"✅ Конфигурация загружена")
print(f"📢 Канал: {CHANNEL_USERNAME}")
print(f"👥 Админов: {len(ADMIN_IDS)}")
print(f"🔑 ADMIN_IDS: {ADMIN_IDS}")

# Flask и бот
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

stats = {'start_time': datetime.now(), 'messages': 0}


def is_admin(user_id):
    """Проверка админа"""
    result = user_id in ADMIN_IDS
    print(f"🔍 Проверка админа: user_id={user_id}, is_admin={result}, ADMIN_IDS={ADMIN_IDS}")
    return result


def create_button():
    """Создание кнопки WebApp"""
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton(
        text="📱 Открыть каталог",
        web_app=telebot.types.WebAppInfo(url=WEBAPP_URL)
    )
    markup.add(btn)
    return markup


# ========== ОБРАБОТЧИКИ БОТА ==========

@bot.message_handler(commands=['start'])
def start_cmd(message):
    """Команда /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    print(f"📨 [START] user_id={user_id}, username=@{username}")
    
    if is_admin(user_id):
        text = (
            "👋 <b>Привет, админ!</b>\n\n"
            "📋 <b>Инструкция:</b>\n"
            f"1. Отправь мне пост (текст/фото/видео)\n"
            f"2. Добавь хэштег <code>{TRIGGER_HASHTAG}</code>\n"
            f"3. Пост опубликуется в {CHANNEL_USERNAME} с кнопкой!\n\n"
            f"<b>Твой ID:</b> <code>{user_id}</code>\n"
            f"<b>Статус:</b> ✅ Админ"
        )
    else:
        text = (
            f"❌ <b>Доступ запрещён</b>\n\n"
            f"Твой ID: <code>{user_id}</code>\n"
            f"Ты не админ этого бота."
        )
    
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_message(message):
    """Обработка всех сообщений"""
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    print(f"📨 [MESSAGE] user_id={user_id}, username=@{username}, type={message.content_type}")
    
    # Проверка админа
    if not is_admin(user_id):
        print(f"❌ [UNAUTHORIZED] user_id={user_id} НЕ в списке админов {ADMIN_IDS}")
        bot.send_message(message.chat.id, "❌ У вас нет прав")
        return
    
    # Извлекаем текст
    text = message.caption if message.caption else (message.text if message.text else "")
    
    print(f"📝 Текст сообщения: {text[:50]}...")
    
    # Проверка хэштега
    if TRIGGER_HASHTAG.lower() not in text.lower():
        print(f"⚠️ Хэштег {TRIGGER_HASHTAG} не найден")
        return
    
    print(f"✅ Хэштег найден! Публикую в канал...")
    
    try:
        # Копируем в канал
        sent = bot.copy_message(
            chat_id=CHANNEL_USERNAME,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        
        print(f"✅ Сообщение скопировано, message_id={sent.message_id}")
        
        # Добавляем кнопку
        try:
            bot.edit_message_reply_markup(
                chat_id=CHANNEL_USERNAME,
                message_id=sent.message_id,
                reply_markup=create_button()
            )
            print(f"✅ Кнопка добавлена")
        except Exception as e:
            print(f"⚠️ Не удалось добавить кнопку: {e}")
            bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text="👆 Смотрите пост выше",
                reply_markup=create_button()
            )
        
        # Удаляем оригинал
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        
        # Уведомление
        bot.send_message(
            message.chat.id,
            f"✅ <b>Опубликовано!</b>\n\n📢 {CHANNEL_USERNAME}",
            parse_mode='HTML'
        )
        
        print(f"🎉 Публикация успешна!")
        
    except Exception as e:
        print(f"❌ ОШИБКА публикации: {e}")
        bot.send_message(
            message.chat.id,
            f"❌ <b>Ошибка:</b>\n{str(e)}",
            parse_mode='HTML'
        )


# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    """Главная страница"""
    uptime = datetime.now() - stats['start_time']
    return f"""
    <html>
    <body style="font-family: Arial; background: #667eea; color: white; text-align: center; padding: 50px;">
        <h1>🤖 ARCTURUS Bot</h1>
        <p>✅ Работает {int(uptime.total_seconds()/3600)}ч {int((uptime.total_seconds()%3600)/60)}м</p>
        <p>📨 Сообщений: {stats['messages']}</p>
        <p>👥 Админов: {len(ADMIN_IDS)}</p>
        <p>📢 Канал: {CHANNEL_USERNAME}</p>
    </body>
    </html>
    """


@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'uptime': int((datetime.now() - stats['start_time']).total_seconds())}), 200


@app.route('/webhook_info')
def webhook_info():
    """Информация о webhook"""
    try:
        info = bot.get_webhook_info()
        return jsonify({
            'url': info.url,
            'pending_update_count': info.pending_update_count,
            'last_error_message': info.last_error_message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/set_webhook')
def set_webhook_route():
    """Установка webhook"""
    try:
        webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        print(f"✅ Webhook установлен: {webhook_url}")
        return jsonify({
            'status': 'success',
            'url': webhook_url
        })
    except Exception as e:
        print(f"❌ Ошибка установки webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Обработка webhook от Telegram"""
    stats['messages'] += 1
    
    print(f"\n🔔 WEBHOOK ВЫЗВАН! Всего сообщений: {stats['messages']}")
    
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        print(f"📦 Получены данные: {json_string[:200]}...")
        
        update = telebot.types.Update.de_json(json_string)
        print(f"📨 Update ID: {update.update_id}")
        
        if update.message:
            print(f"👤 От пользователя: {update.message.from_user.id}")
        
        bot.process_new_updates([update])
        print(f"✅ Update обработан\n")
        
        return '', 200
    else:
        print(f"❌ Неверный content-type: {request.headers.get('content-type')}")
        return 'Invalid content type', 403


# ========== STARTUP ==========

if __name__ == '__main__':
    print("🚀 Запуск бота...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)