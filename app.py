"""
Flask приложение для Telegram бота
Обрабатывает webhook от Telegram и раздаёт статические файлы
"""

import os
import telebot
from flask import Flask, request, send_from_directory, jsonify
from datetime import datetime
from bot.config import Config
from bot.main import create_bot, setup_webhook


# Создание Flask приложения
app = Flask(__name__, static_folder='web', static_url_path='')
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Создание бота
bot = create_bot()

# Статистика
stats = {
    'start_time': datetime.now(),
    'webhook_calls': 0,
    'health_checks': 0
}


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Главная страница - показывает статус бота"""
    uptime = datetime.now() - stats['start_time']
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    
    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ARCTURUS_TGBot</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                padding: 20px;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }}
            h1 {{
                font-size: 2.5rem;
                margin-bottom: 10px;
                text-align: center;
            }}
            .status {{
                text-align: center;
                font-size: 1.2rem;
                margin-bottom: 30px;
                opacity: 0.9;
            }}
            .stats {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .stat-row {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .stat-row:last-child {{
                border-bottom: none;
            }}
            .stat-label {{
                opacity: 0.8;
            }}
            .stat-value {{
                font-weight: bold;
            }}
            .indicator {{
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #4ade80;
                animation: pulse 2s infinite;
                margin-right: 8px;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}
            .time {{
                text-align: center;
                font-size: 0.9rem;
                opacity: 0.7;
                margin-top: 20px;
            }}
            .links {{
                display: flex;
                gap: 10px;
                margin-top: 20px;
                flex-wrap: wrap;
            }}
            .link {{
                flex: 1;
                min-width: 150px;
                padding: 12px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                text-align: center;
                text-decoration: none;
                color: white;
                transition: all 0.3s;
            }}
            .link:hover {{
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 ARCTURUS_TGBot</h1>
            <div class="status">
                <span class="indicator"></span>Бот работает
            </div>
            
            <div class="stats">
                <div class="stat-row">
                    <span class="stat-label">Время работы:</span>
                    <span class="stat-value">{hours}ч {minutes}м</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Webhook вызовов:</span>
                    <span class="stat-value">{stats['webhook_calls']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Health checks:</span>
                    <span class="stat-value">{stats['health_checks']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Канал:</span>
                    <span class="stat-value">{Config.CHANNEL_USERNAME}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Админов:</span>
                    <span class="stat-value">{len(Config.ADMIN_IDS)}</span>
                </div>
            </div>
            
            <div class="links">
                <a href="/health" class="link">📊 Health Check</a>
                <a href="/webhook_info" class="link">🔗 Webhook Info</a>
                <a href="{Config.WEBAPP_URL}" target="_blank" class="link">🌐 WebApp</a>
            </div>
            
            <div class="time">
                Текущее время: <span id="time"></span>
            </div>
        </div>
        
        <script>
            function updateTime() {{
                const now = new Date();
                document.getElementById('time').textContent = now.toLocaleString('ru-RU');
            }}
            updateTime();
            setInterval(updateTime, 1000);
        </script>
    </body>
    </html>
    """


@app.route('/health')
def health():
    """Health check для UptimeRobot"""
    stats['health_checks'] += 1
    
    return jsonify({
        'status': 'healthy',
        'bot': 'running',
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': int((datetime.now() - stats['start_time']).total_seconds()),
        'webhook_calls': stats['webhook_calls']
    }), 200


@app.route('/webhook_info')
def webhook_info():
    """Информация о webhook"""
    try:
        info = bot.get_webhook_info()
        return jsonify({
            'url': info.url,
            'has_custom_certificate': info.has_custom_certificate,
            'pending_update_count': info.pending_update_count,
            'last_error_date': info.last_error_date,
            'last_error_message': info.last_error_message,
            'max_connections': info.max_connections
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/set_webhook')
def set_webhook():
    """Установка webhook (вызвать один раз после деплоя)"""
    try:
        success = setup_webhook(bot)
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Webhook установлен успешно',
                'url': Config.get_webhook_url()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Не удалось установить webhook'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route(f'/{Config.BOT_TOKEN}', methods=['POST'])
def webhook():
    """Обработка webhook от Telegram"""
    stats['webhook_calls'] += 1
    
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid content type', 403


# Раздача статических файлов из папки web/
@app.route('/<path:path>')
def serve_static(path):
    """Раздача статических файлов"""
    return send_from_directory('web', path)


# ==================== STARTUP ====================

@app.before_request
def before_first_request():
    """Инициализация при первом запросе"""
    if not hasattr(app, 'webhook_set'):
        # Устанавливаем webhook автоматически при первом запуске
        if Config.RENDER_URL and not Config.DEBUG:
            setup_webhook(bot)
        app.webhook_set = True


# ==================== MAIN ====================

if __name__ == '__main__':
    # Локальный запуск (для тестирования)
    print("⚠️ Локальный режим - используйте polling вместо webhook")
    print("Для production используйте: gunicorn app:app")
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )