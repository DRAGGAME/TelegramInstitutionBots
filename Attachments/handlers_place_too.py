import io
import os
import uuid
from pytz import timezone
from aiogram import Router, F, types, Bot
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters.command import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from collections import OrderedDict
from aiogram.types import Message
from db.db import Sqlbase
from datetime import datetime
from aiogram.types.input_file import BufferedInputFile

'''Для работы с .env'''

from dotenv import load_dotenv

load_dotenv = load_dotenv()
bot = Bot(token=os.getenv('API_KEY'))
router = Router()
rating = ("1", "2", "3", "4", "5", "назад", "Назад")
sqlbase = Sqlbase()


# Определяем состояния для FSM
class Rev(StatesGroup):
    user_id = State()
    user_address = State()
    user_place = State()
    user_rating = State()
    user_reply = State()
    user_review = State()


@router.message(F.text.in_('Написать новый отзыв'))
@router.message(CommandStart())
async def starts(message: Message, state: FSMContext):
    await sqlbase.connect()

    # Загружаем адреса из базы
    addres = await sqlbase.execute_query('SELECT address FROM message ORDER BY id ASC')
    first = {row[0] for row in addres}

    # Сохраняем адреса в состояние
    await state.update_data(locales=list(first))

    # Создаём клавиатуру
    kb = [[types.KeyboardButton(text=firs)] for firs in first]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder='Введите место')
    await message.answer('Здравствуйте, выберите адрес:', reply_markup=keyboard)
    await state.set_state(Rev.user_address)


@router.message(Rev.user_address)
async def user_address_(message: Message, state: FSMContext):
    data = await state.get_data()
    locales = data.get("locales", [])

    #Проверка на локации
    if message.text not in locales:
        await message.reply('Можно ввести символы, только те, которые имеются на клавиатуре')
        return

    await state.update_data(user_address=message.text)

    places = await sqlbase.execute_query(f'SELECT place FROM message WHERE address = $1 ORDER BY id ASC' , (message.text,))
    first_place = {row[0] for row in places}

    await state.update_data(locales_for_address=list(first_place))

    kb = [[types.KeyboardButton(text=placen)] for placen in first_place]
    kb.append([types.KeyboardButton(text="Назад")])


    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder='Введите место')
    await message.answer('Выберите место:', reply_markup=keyboard)
    await state.set_state(Rev.user_place)


@router.message(Rev.user_place)
async def user_place_(message: Message, state: FSMContext):
    data = await state.get_data()
    locales_for_address = data.get("locales_for_address", [])

    if 'назад' in message.text.lower():
        await state.set_state(Rev.user_address)
        data = await state.get_data()
        first = data.get('locales', [])
        kb = [[types.KeyboardButton(text=firs)] for firs in first]
        # kb.append([types.KeyboardButton(text="Назад")])
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder='Введите место')
        await message.answer('Здравствуйте, выберите адрес:', reply_markup=keyboard)
        return

    if message.text not in locales_for_address :
        await message.reply('Можно ввести символы, только те, которые имеются на клавиатуре')
        return

    await state.update_data(user_place=message.text)

    value_place = message.text
    messagen = await sqlbase.execute_query(
        'SELECT message, photo FROM message WHERE place = $1', (value_place,)
    )

    # Преобразование данных из базы в BytesIO
    img_byte_arr = io.BytesIO(messagen[0][1])

    # Проверка, что файл не пуст
    if img_byte_arr.getbuffer().nbytes == 0:
        await message.reply("Файл изображения пуст или поврежден.")
        return

    img_byte_arr.seek(0)

    builder = ReplyKeyboardBuilder()

    for i in range(1, 6):
        builder.add(types.KeyboardButton(text=str(i)))
    builder.add(types.KeyboardButton(text="Назад"))
    builder.adjust(5,1)
    chat_ids = message.from_user.id
    rd = str(uuid.uuid4().int)[:6]
    input_file = BufferedInputFile(file=img_byte_arr.read(), filename=f"image{rd}.jpg")
    await bot.send_photo(chat_id=chat_ids, caption=f'{messagen[0][0]}\nОцените наше заведение', photo=input_file,
                         reply_markup=builder.as_markup(resize_keyboard=True))

    await state.set_state(Rev.user_rating)


@router.message(Rev.user_rating, F.text.in_(rating))
async def user_rating_(message: Message, state: FSMContext):
    if 'назад' in message.text.lower():

        await state.set_state(Rev.user_place)
        data = await state.get_data()
        first = data.get('locales_for_address', [])
        kb = [[types.KeyboardButton(text=firs)] for firs in first]
        kb.append([types.KeyboardButton(text='Назад')])

        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder='Введите оценку')
        await message.answer('Здравствуйте, выберите место:', reply_markup=keyboard)
        return
    await state.update_data(user_rating=message.text)

    keb = [[types.KeyboardButton(text='Да'), types.KeyboardButton(text='Нет')],
           [types.KeyboardButton(text='Назад')]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=keb, resize_keyboard=True, input_field_placeholder='Хотите написать ли вы отзыв')
    await message.answer(
        'Оценка принята. Если вы желаете написать отзыв, то напишите "Да", если нет, то "Нет".',
        reply_markup=keyboard
    )
    await state.set_state(Rev.user_reply)


@router.message(F.text.in_(['Да', 'да', 'Нет', 'нет', 'назад', 'Назад']), Rev.user_reply)
async def rat(message: Message, state: FSMContext):
    user_input = message.text
    if 'назад' in message.text.lower():
        await state.set_state(Rev.user_rating)
        builder = ReplyKeyboardBuilder()
        for i in range(1, 6):
            builder.add(types.KeyboardButton(text=str(i)))
        builder.add(types.KeyboardButton(text="Назад"))
        builder.adjust(5, 1)
        await message.answer('Здравствуйте, выберите оценку:', reply_markup=builder.as_markup(resize_keyboard=True,
                                                                                              input_field_placeholder=
                                                                                              'Введите оценку'))

    if user_input in ['Да', 'да']:
        await message.answer('Напишите, пожалуйста, отзыв', input_field_placeholder='Напишите отзыв', reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Rev.user_review)

    elif user_input in ['Нет', 'нет']:
        builder = ReplyKeyboardBuilder()

        builder.add(types.KeyboardButton(text='Написать новый отзыв'))

        moscow_tz = timezone("Europe/Moscow")
        current_datetime = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
        data = await state.get_data()
        data = OrderedDict(data)
        data['id_user'] = message.from_user.username
        await sqlbase.ins(current_datetime, data['user_address'], data['user_place'], data['id_user'], int(data['user_rating']), 'Нет')
        await message.answer('Спасибо за оценку нашего заведения!', reply_markup=builder.as_markup(resize_keyboard=True))
        await sqlbase.close()
        await bot.session.close()  # Закрытие сессии бота

        await state.clear()


@router.message(Rev.user_review)
async def save_reviewer(message: Message, state: FSMContext):
    builder = ReplyKeyboardBuilder()
    moscow_tz = timezone("Europe/Moscow")
    current_datetime = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
    if message.sticker:
        await message.answer('Не отправляйте стикером, бот его не обработает')
        return
    await state.update_data(user_review=message.text)
    builder.add(types.KeyboardButton(text='Написать новый отзыв'))

    data = await state.get_data()
    data = OrderedDict(data)
    data['id_user'] = message.from_user.username

    await sqlbase.ins(current_datetime, data['user_address'], data['user_place'], data['id_user'], int(data['user_rating']), data['user_review'])
    await message.answer('Спасибо за оценку и отзыв нашего заведения!', reply_markup=builder.as_markup(resize_keyboard=True))
    await sqlbase.close()
    await bot.session.close()  # Закрытие сессии бота
    await state.clear()

@router.message(Rev.user_rating, ~F.text.in_(rating))
async def not_text(message: Message):
    await message.answer('Можно ввести символы, только те, какие есть в кнопках')