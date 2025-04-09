import logging
import asyncio
import os
from aiogram import Bot, Dispatcher
from Attachments import handlers_place_one, handlers_place_too

'''Для работы с .env'''

from dotenv import load_dotenv

load_dotenv = load_dotenv()
logging.basicConfig(level=logging.DEBUG)
BOT = Bot(token=os.getenv('API_KEY'))
dp = Dispatcher()

dp.include_router(handlers_place_one.router)
dp.include_router(handlers_place_too.router)

async def main():
    await dp.start_polling(BOT)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        BOT.session.close()
