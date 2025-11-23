"""
Конфигурация бота - ИСПРАВЛЕНО
"""

import os
from typing import List

class Config:
    """Конфигурация приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.environ.get('BOT_TOKEN', '')
    CHANNEL_USERNAME: str = os.environ.get('CHANNEL_USERNAME', '')
    
    # WebApp URL
    WEBAPP_URL: str = os.environ.get('WEBAPP_URL', '')
    
    # ИСПРАВЛЕНО: Единственный админ ID
    ADMIN_ID: int = int(os.environ.get('ADMIN_ID', '0'))
    
    # Render
    RENDER_URL: str = os.environ.get('RENDER_URL', '')
    PORT: int = int(os.environ.get('PORT', 10000))
    
    # Хэштег для публикации
    TRIGGER_HASHTAG: str = '#arcturus'
    
    # Flask (минимум)
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка наличия всех необходимых переменных"""
        missing = []
        
        if not cls.BOT_TOKEN:
            missing.append('BOT_TOKEN')
        if not cls.CHANNEL_USERNAME:
            missing.append('CHANNEL_USERNAME')
        if not cls.WEBAPP_URL:
            missing.append('WEBAPP_URL')
        if not cls.RENDER_URL:
            missing.append('RENDER_URL')
        if cls.ADMIN_ID == 0:
            missing.append('ADMIN_ID')
        
        if missing:
            print(f"❌ Отсутствуют переменные: {', '.join(missing)}")
            return False
        
        print("✅ Все переменные окружения на месте")
        print(f"👤 Admin ID: {cls.ADMIN_ID}")
        return True
    
    @classmethod
    def get_webhook_url(cls) -> str:
        """Получить URL вебхука"""
        return f"{cls.RENDER_URL}/{cls.BOT_TOKEN}"