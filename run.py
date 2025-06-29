import asyncio
import logging

from aiogram import Dispatcher
from config import bot
from handlers import handlers_for_review

'''Для работы с .env'''
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] #%(levelname)-4s %(filename)s:'
                    '%(lineno)d - %(name)s - %(message)s'
                    )


dp = Dispatcher()

dp.include_router(handlers_for_review.router)

async def main():

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


