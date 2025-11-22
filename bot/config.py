"""
Конфигурация бота
Все чувствительные данные берутся из переменных окружения
"""

import os
from typing import List

class Config:
    """Конфигурация приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.environ.get('BOT_TOKEN', '')
    CHANNEL_USERNAME: str = os.environ.get('CHANNEL_USERNAME', '')
    
    # WebApp
    WEBAPP_URL: str = os.environ.get('WEBAPP_URL', '')
    
    # Администраторы (ID через запятую)
    ADMIN_IDS: List[int] = [
        int(id.strip()) 
        for id in os.environ.get('ADMIN_IDS', '').split(',') 
        if id.strip()
    ]
    
    # Render
    RENDER_URL: str = os.environ.get('RENDER_URL', '')
    PORT: int = int(os.environ.get('PORT', 10000))
    
    # Хэштег для публикации
    TRIGGER_HASHTAG: str = '#arcturus'
    
    # Flask
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка наличия всех необходимых переменных"""
        required = [
            cls.BOT_TOKEN,
            cls.CHANNEL_USERNAME,
            cls.WEBAPP_URL,
            cls.RENDER_URL
        ]
        
        if not all(required):
            missing = []
            if not cls.BOT_TOKEN: missing.append('BOT_TOKEN')
            if not cls.CHANNEL_USERNAME: missing.append('CHANNEL_USERNAME')
            if not cls.WEBAPP_URL: missing.append('WEBAPP_URL')
            if not cls.RENDER_URL: missing.append('RENDER_URL')
            
            print(f"❌ Отсутствуют переменные окружения: {', '.join(missing)}")
            return False
        
        if not cls.ADMIN_IDS:
            print("⚠️ Предупреждение: не указаны ADMIN_IDS")
        
        return True
    
    @classmethod
    def get_webhook_url(cls) -> str:
        """Получить URL вебхука"""
        return f"{cls.RENDER_URL}/{cls.BOT_TOKEN}"