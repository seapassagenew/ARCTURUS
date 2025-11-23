"""
Основной модуль Telegram бота
"""

import telebot
from bot.config import Config
from bot.handlers import register_handlers


def create_bot() -> telebot.TeleBot:
    """
    Создание и настройка бота
    
    Returns:
        Настроенный экземпляр TeleBot
    """
    # Валидация конфигурации
    if not Config.validate():
        raise ValueError("Неверная конфигурация бота. Проверьте переменные окружения.")
    
    # Создание бота
    bot = telebot.TeleBot(
        Config.BOT_TOKEN,
        parse_mode=None,
        threaded=True
    )
    
    # Регистрация обработчиков
    register_handlers(bot)
    
    print("✅ Бот создан успешно")
    print(f"📱 WebApp URL: {Config.WEBAPP_URL}")
    print(f"📢 Канал: {Config.CHANNEL_USERNAME}")
    print(f"👥 Админов: {len(Config.ADMIN_ID)}")
    
    return bot


def setup_webhook(bot: telebot.TeleBot) -> bool:
    """
    Настройка webhook для бота
    
    Args:
        bot: Экземпляр TeleBot
    
    Returns:
        True если webhook установлен успешно
    """
    try:
        webhook_url = Config.get_webhook_url()
        
        # Удаляем старый webhook
        bot.remove_webhook()
        print("🗑️ Старый webhook удалён")
        
        # Устанавливаем новый webhook
        bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        
        print(f"✅ Webhook установлен: {webhook_url}")
        
        # Проверяем webhook
        webhook_info = bot.get_webhook_info()
        print(f"📊 Webhook Info:")
        print(f"   URL: {webhook_info.url}")
        print(f"   Pending updates: {webhook_info.pending_update_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка установки webhook: {e}")
        return False


def run_polling(bot: telebot.TeleBot):
    """
    Запуск бота в режиме polling (для локальной разработки)
    
    Args:
        bot: Экземпляр TeleBot
    """
    print("🚀 Запуск бота в режиме polling...")
    print("⚠️ Этот режим только для локальной разработки!")
    
    # Удаляем webhook перед polling
    bot.remove_webhook()
    
    # Запускаем бота
    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=30,
        allowed_updates=['message']
    )


if __name__ == "__main__":
    # Для локального тестирования
    bot = create_bot()
    run_polling(bot)