"""
Flask приложение для Telegram бота
Минималистичная версия - только webhook и безопасность
"""

import telebot
from flask import Flask, request, jsonify
from datetime import datetime
from bot.config import Config
from bot.main import create_bot, setup_webhook

# Flask приложение
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Создание бота
bot = create_bot()

# Статистика (минимум)
stats = {
    'start_time': datetime.now(),
    'webhook_calls': 0
}

print(f"🚀 Бот запущен!")
print(f"📱 Ваш ID должен быть в ADMIN_IDS: {Config.ADMIN_IDS}")
print(f"📢 Канал: {Config.CHANNEL_USERNAME}")
print(f"🔗 Webhook URL: {Config.get_webhook_url()}")


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Минимальная главная страница"""
    return jsonify({
        'status': 'running',
        'bot': 'ARCTURUS_TGBot',
        'uptime_seconds': int((datetime.now() - stats['start_time']).total_seconds())
    }), 200


@app.route('/health')
def health():
    """Health check для UptimeRobot и Render"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/webhook_info')
def webhook_info():
    """Проверка webhook"""
    try:
        info = bot.get_webhook_info()
        return jsonify({
            'url': info.url,
            'pending_updates': info.pending_update_count,
            'last_error': info.last_error_message,
            'webhook_calls': stats['webhook_calls']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/setup_webhook')
def set_webhook_route():
    """Установка webhook вручную"""
    try:
        success = setup_webhook(bot)
        if success:
            return jsonify({
                'status': 'success',
                'webhook_url': Config.get_webhook_url()
            }), 200
        else:
            return jsonify({'status': 'error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route(f'/{Config.BOT_TOKEN}', methods=['POST'])
def webhook():
    """Обработка webhook от Telegram"""
    stats['webhook_calls'] += 1
    
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            
            # Логируем входящие обновления для отладки
            if update.message:
                user_id = update.message.from_user.id
                username = update.message.from_user.username
                text = update.message.text or update.message.caption or "[media]"
                print(f"📨 Сообщение от @{username} (ID: {user_id}): {text[:50]}")
            
            bot.process_new_updates([update])
            return '', 200
        else:
            return 'Invalid content type', 403
    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")
        return '', 500


# ==================== STARTUP ====================

def init_webhook():
    """Инициализация webhook при запуске"""
    if Config.RENDER_URL and not Config.DEBUG:
        print("🔧 Установка webhook...")
        success = setup_webhook(bot)
        if success:
            print("✅ Webhook установлен успешно")
        else:
            print("⚠️ Не удалось установить webhook автоматически")
            print("👉 Вызовите вручную: /setup_webhook")


# Устанавливаем webhook при первом запросе
@app.before_request
def before_first_request():
    if not hasattr(app, '_webhook_initialized'):
        init_webhook()
        app._webhook_initialized = True


if __name__ == '__main__':
    print("⚠️ Локальный режим!")
    print("Для production используйте: gunicorn app:app")
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )