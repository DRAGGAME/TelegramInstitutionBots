import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
import asyncpg

# Настройки
BOT_TOKEN = "your_bot_token"
DB_PARAMS = {
    "user": "your_username",
    "password": "your_password",
    "database": "your_database",
    "host": "localhost"
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def notify_listener():
    conn = await asyncpg.connect(**DB_PARAMS)
    await conn.add_listener('new_review', handle_new_review)
    print("Слушаем канал new_review...")

async def handle_new_review(connection, pid, channel, payload):
    # payload содержит данные из pg_notify
    print(f"Получено уведомление: {payload}")
    # Отправляем сообщение в Telegram
    await bot.send_message(chat_id="your_chat_id", text=f"Новый отзыв: {payload}")

async def main():
    # Запускаем слушатель уведомлений и бота
    await asyncio.gather(notify_listener(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
