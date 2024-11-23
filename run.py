import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from Attachments import handlers

logging.basicConfig(level=logging.INFO)

load_dotenv()

bot = Bot(token='7640173961:AAHQHzALV1xEW4meqxL0hfsHdSd7vjjmRRg')
dp = Dispatcher()


dp.include_router(handlers.router)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass