import base64
import io
import os
from pytz import timezone
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Router, F, types, Bot
from aiogram.types import Message, BufferedInputFile
from aiogram.filters.command import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from collections import OrderedDict
from uuid import uuid4
from datetime import datetime
from db.db import Sqlbase

'''Для работы с .env'''

from dotenv import load_dotenv

load_dotenv = load_dotenv()
bot = Bot(token=os.getenv('API_KEY'))

router = Router()
rating = ["1", '2', '3', '4', '5']
sqlbase = Sqlbase()


class Review(StatesGroup):
    user_id = State()
    user_place = State()
    user_rating = State()
    user_review = State()

def decode_data(encoded_text):
    try:
        return base64.urlsafe_b64decode(encoded_text.encode('utf-8')).decode('utf-8')
    except Exception:
        return None

@router.message(CommandStart(deep_link=True))
async def start_with_deep_link(message: Message, state: FSMContext):
    await sqlbase.connect()

    # Извлечение и обработка deep_link аргумента
    if message.text and len(message.text.split()) > 1:
        encoded_arg = message.text.split()[1]
        place_name = decode_data(encoded_arg)  # Декодируем название места
        if place_name:
            await state.update_data(user_place=place_name)

            # Выполняем запрос к базе данных
            messagen = await sqlbase.execute_query(
                'SELECT message, photo FROM message WHERE place = $1', (place_name,)
            )

            if not messagen or not messagen[0][1]:  # Если данных нет или изображение отсутствует
                await message.reply("Не удалось найти сообщение или изображение для указанного места.")
                return

            # Преобразуем данные изображения в BytesIO
            try:
                img_byte_arr = io.BytesIO(messagen[0][1])
                if img_byte_arr.getbuffer().nbytes == 0:
                    raise ValueError("Файл изображения пуст.")
                img_byte_arr.seek(0)
            except Exception as e:
                await message.reply(f"Ошибка при обработке изображения: {str(e)}")
                return

            # Создаем клавиатуру для оценки
            builder = ReplyKeyboardBuilder()
            for i in range(1, 6):  # Оценки от 1 до 5
                builder.add(types.KeyboardButton(text=str(i)))
            builder.adjust(5)

            # Отправляем фото и сообщение пользователю
            try:
                chat_ids = message.from_user.id
                file_name = f"image_{uuid4().hex}.jpg"  # Уникальное имя файла
                input_file = BufferedInputFile(file=img_byte_arr.read(), filename=file_name)

                await bot.send_photo(
                    chat_id=chat_ids,
                    caption=f'{messagen[0][0]}\nОцените наше заведение',
                    photo=input_file,
                    reply_markup=builder.as_markup(resize_keyboard=True)
                )
                await state.set_state(Review.user_rating)
            except Exception as e:
                await message.reply(f"Ошибка при отправке изображения: {str(e)}")
        else:
            await message.answer("Некорректная ссылка или место не найдено.")
    else:
        await message.answer("Не указан deep_link аргумент.")



@router.message(Review.user_rating, F.text.in_(rating))
async def too(message: Message, state: FSMContext):
    await state.update_data(user_rating=message.text)
    kb = [
        [types.KeyboardButton(text='Да'), types.KeyboardButton(text='Нет')],

    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder='Введите да или нет')
    await message.answer('Оценка принята\nЕсли вы желаете написать отзыв, то напишите "Да", если нет, то соответственно', reply_markup=keyboard)


@router.message(F.text.in_(['Да','да','Нет','нет']), Review.user_rating)
async def rat(message: Message, state: FSMContext):
    user_input = message.text

    if user_input in ['Да', 'да']:
        await message.answer('Напишите пожалуйста отзыв', input_field_placeholder='Напишите отзыв',reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Review.user_review)

    elif user_input in ['Нет', 'нет']:
        moscow_tz = timezone("Europe/Moscow")
        current_datetime = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')

        data = await state.get_data()

        data = OrderedDict(data)
        data['id_user'] = message.from_user.username
        await message.answer(f'Спасибо за оценку нашего заведения!', reply_markup=types.ReplyKeyboardRemove())

        await sqlbase.ins_ins(current_datetime, data['user_place'], data['id_user'],  int(data['user_rating']), 'Нет')
        await sqlbase.close()
        await bot.session.close()  # Закрытие сессии бота

        await state.clear()



@router.message(Review.user_review)
async def save_review(message: Message, state: FSMContext):
    moscow_tz = timezone("Europe/Moscow")
    current_datetime = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
    if message.sticker:
        await message.answer('Не отправляйте стикером, бот его не обработает')
        return
    await state.update_data(user_review=message.text)

    data = await state.get_data()
    data = OrderedDict(data)
    data['id_user'] = message.from_user.username
    await message.answer(f'Спасибо за оценку и отзыв нашего заведения!', reply_markup=types.ReplyKeyboardRemove())

    await sqlbase.ins_ins(current_datetime,
                        data['user_place'],
                        data['id_user'],
                        int(data['user_rating']),
                        data['user_review'])
    await sqlbase.close()
    await bot.session.close()  # Закрытие сессии бота
    await state.clear()


@router.message(Review.user_rating, ~F.text.in_(rating))
async def too(message: Message):
    await message.reply('Можно ввести символы, только те, которые имеются на клавиатуре')




