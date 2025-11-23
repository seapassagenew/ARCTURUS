"""
Flask приложение для ARCTURUS_Bot - ИСПРАВЛЕНО!
Проблема была: бот не обрабатывал updates из webhook
"""

import telebot
from flask import Flask, request, jsonify
from bot.config import Config
from bot.main import create_bot

# Flask приложение
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Создание бота
print("=" * 70)
print("🤖 СОЗДАНИЕ БОТА...")
print("=" * 70)

bot = create_bot()

print("=" * 70)
print("✅ БОТ СОЗДАН!")
print("=" * 70)

# Счётчик webhook
webhook_count = 0


@app.route('/')
def index():
    """Простая страница статуса"""
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
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #667eea; }}
            .status {{ color: #4ade80; font-weight: bold; }}
            .info {{ 
                background: #f9fafb;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 ARCTURUS Bot</h1>
            <p class="status">✅ Бот работает</p>
            <div class="info">
                <p><strong>Канал:</strong> {Config.CHANNEL_USERNAME}</p>
                <p><strong>Admin ID:</strong> {Config.ADMIN_ID}</p>
                <p><strong>Webhook вызовов:</strong> {webhook_count}</p>
                <p><strong>WebApp:</strong> <a href="{Config.WEBAPP_URL}" target="_blank">Открыть</a></p>
            </div>
            <p><a href="/health">Health Check</a> | <a href="/webhook_info">Webhook Info</a></p>
        </div>
    </body>
    </html>
    """


@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'bot': 'running',
        'webhook_calls': webhook_count
    }), 200


@app.route('/webhook_info')
def webhook_info():
    """Информация о webhook"""
    try:
        info = bot.get_webhook_info()
        return jsonify({
            'url': info.url,
            'pending_updates': info.pending_update_count,
            'last_error': info.last_error_message,
            'last_error_date': info.last_error_date
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/set_webhook')
def set_webhook_route():
    """Установка webhook вручную"""
    try:
        webhook_url = Config.get_webhook_url()
        
        # Удаляем старый
        bot.remove_webhook()
        print("🗑️ Старый webhook удалён")
        
        # Устанавливаем новый с allowed_updates
        bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "channel_post"]  # ← ИСПРАВЛЕНО!
        )
        
        print(f"✅ Webhook установлен: {webhook_url}")
        
        # Проверяем
        info = bot.get_webhook_info()
        
        return jsonify({
            'status': 'success',
            'webhook_url': webhook_url,
            'pending_updates': info.pending_update_count,
            'allowed_updates': info.allowed_updates
        })
        
    except Exception as e:
        print(f"❌ Ошибка установки webhook: {e}")
        return jsonify({'error': str(e)}), 500


@app.route(f'/{Config.BOT_TOKEN}', methods=['POST'])
def webhook():
    """
    КРИТИЧЕСКИ ВАЖНО!
    Обработка webhook от Telegram
    """
    global webhook_count
    webhook_count += 1
    
    try:
        # Проверяем Content-Type
        if request.headers.get('content-type') != 'application/json':
            print(f"⚠️ Неверный Content-Type: {request.headers.get('content-type')}")
            return 'Invalid content type', 403
        
        # Получаем JSON
        json_string = request.get_data().decode('utf-8')
        
        # ВАЖНО! Логируем что пришло
        print(f"📥 Webhook #{webhook_count}: {json_string[:200]}...")
        
        # Парсим update
        update = telebot.types.Update.de_json(json_string)
        
        # КРИТИЧНО! Обрабатываем update
        bot.process_new_updates([update])
        
        print(f"✅ Update #{webhook_count} обработан")
        
        return '', 200
        
    except Exception as e:
        print(f"❌ Ошибка обработки webhook: {e}")
        import traceback
        traceback.print_exc()
        return '', 500


@app.before_request
def setup_webhook_once():
    """Автоматическая установка webhook при первом запросе"""
    if not hasattr(app, 'webhook_initialized'):
        try:
            webhook_url = Config.get_webhook_url()
            
            print("=" * 70)
            print("🔄 УСТАНОВКА WEBHOOK...")
            print("=" * 70)
            
            # Удаляем старый
            bot.remove_webhook()
            print("🗑️ Старый webhook удалён")
            
            # КРИТИЧНО! Указываем какие updates принимать
            bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "channel_post"]  # ← ИСПРАВЛЕНО!
            )
            
            print(f"✅ Webhook установлен: {webhook_url}")
            print(f"📋 Allowed updates: message, channel_post")
            
            # Проверяем
            info = bot.get_webhook_info()
            print(f"📊 Pending updates: {info.pending_update_count}")
            print(f"📋 Allowed updates: {info.allowed_updates}")
            
            app.webhook_initialized = True
            
            print("=" * 70)
            print("✅ WEBHOOK ГОТОВ!")
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ Ошибка webhook: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 ЗАПУСК FLASK...")
    print("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=False
    )