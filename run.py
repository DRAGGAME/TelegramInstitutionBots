import logging
import asyncio
import os
import psycopg2

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from Attachments import handlers_place_one, handlers_place_too

logging.basicConfig(level=logging.INFO)

load_dotenv()

BOT_TOKEN = Bot(token= os.getenv('API_KEY'))
dp = Dispatcher()

dp.include_router(handlers_place_one.router)
dp.include_router(handlers_place_too.router)

async def main():
    await dp.start_polling(BOT_TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass