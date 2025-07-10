import io
import uuid
from datetime import datetime

from aiogram import Router, F, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile
from asyncpg import exceptions
from pytz import timezone

from config import bot
from db.db import Sqlbase
from function.decode_data import decode_text
from keyboard.fabirc_kb import KeyboardFactory

router = Router()
rating = ("1", "2", "3", "4", "5", "назад")
sqlbase = Sqlbase()
keyboard_factory = KeyboardFactory()


class Rev(StatesGroup):
    status = State()
    user_id = State()
    user_address = State()
    user_place = State()
    user_rating = State()
    user_reply = State()
    user_review = State()


@router.message(F.text.in_('Отправить новый отзыв'))
@router.message(CommandStart(deep_link=False))
async def starts(message: Message, state: FSMContext):
    """
    Начало для создания отзыва.
    Делаем connect к БД и меняем состояние
    """
    await state.clear()
    await sqlbase.connect()
    """Для выбора адреса"""
    addresses = await sqlbase.execute_query('SELECT address FROM message ORDER BY id ASC')
    addresses = {row[0] for row in addresses}

    kb = await keyboard_factory.builder_reply_text(addresses, "Выберите адрес", False)
    await state.update_data(addresses=addresses, addresses_kb=kb)
    await message.answer('Здравствуйте, выберите адрес:', reply_markup=kb)
    await state.set_state(Rev.user_address)


@router.message(Rev.user_address)
async def user_address_(message: Message, state: FSMContext):
    """Для выбора места по адресу"""

    addresses = await state.get_value("addresses")

    if message.text not in addresses:
        kb = await state.get_value("addresses_kb")
        await message.reply('Можно ввести символы, только те, которые имеются в кнопках\nВыберите адрес',
                            reply_markup=kb)
        return

    user_address = message.text

    places = await sqlbase.execute_query(f'SELECT place FROM message WHERE address = $1 ORDER BY id ASC',
                                         (user_address,))

    all_places = {row[0] for row in places}

    kb = await keyboard_factory.builder_reply_text(all_places, "Выберите место", True)
    await state.update_data(all_places=all_places, user_address=user_address, places_kb=kb)

    await message.answer('Выберите место:', reply_markup=kb)

    await state.set_state(Rev.user_place)


@router.message(CommandStart(deep_link=True))
@router.message(Rev.user_place)
async def user_place_(message: Message, state: FSMContext):
    if 'назад' in message.text.lower():
        await state.set_state(Rev.user_address)
        kb = await state.get_value("addresses_kb")
        await message.answer('Здравствуйте, выберите адрес:', reply_markup=kb)
        return

    all_places = await state.get_value("all_places")

    if message.text and len(message.text.split()) > 1:
        encoded_arg = message.text.split()[1]
        place_name = decode_text(encoded_arg)
        user_place = place_name

    elif message.text not in all_places:
        kb = await state.get_value("places_kb")
        await message.reply('Можно ввести символы, только те, которые имеются в кнопках\nВыберите место',
                            reply_markup=kb)
        return

    else:
        user_place = message.text
    try:
        send_message = await sqlbase.execute_query(
            'SELECT message, photo FROM message WHERE place = $1', (user_place,)
        )
    except exceptions.InterfaceError:
        await sqlbase.connect()
        send_message = await sqlbase.execute_query(
            'SELECT message, photo FROM message WHERE place = $1', (user_place,)
        )

    img_byte_arr = io.BytesIO(send_message[0][1])

    if img_byte_arr.getbuffer().nbytes == 0:
        await message.reply("Файл изображения пуст или поврежден.")
        return

    img_byte_arr.seek(0)

    kb = await keyboard_factory.builder_reply_rating()

    chat_id = message.from_user.id

    rd = str(uuid.uuid4().int)[:6]

    await state.update_data(rating_kb=kb, user_place=user_place)

    input_file = BufferedInputFile(file=img_byte_arr.read(), filename=f"image{rd}.jpg")

    await bot.send_photo(chat_id=chat_id, caption=f'{send_message[0][0]}', photo=input_file,
                         reply_markup=kb)

    await state.set_state(Rev.user_rating)


@router.message(Rev.user_rating, F.text.lower())
async def user_rating_(message: Message, state: FSMContext):
    if message.text.lower() not in rating:
        kb = await state.get_value("rating_kb")

        await message.answer('Можно ввести слова, только те, которые имеются в кнопках', reply_markup=kb)
        return

    if 'назад' in message.text.lower():
        kb = await state.get_value("places_kb")

        await state.set_state(Rev.user_place)
        await message.answer('Здравствуйте, выберите место:', reply_markup=kb)
        return

    msg_review_or_rating = await sqlbase.execute_query(
        '''SELECT review_or_rating_message FROM settings_for_review_bot''')

    kb = await keyboard_factory.builder_reply_choice("Хотите ли вы написать отзыв?")

    await state.update_data(user_rating=message.text, choice_kb=kb)
    await message.answer(
        f'{msg_review_or_rating[0][0]}',
        reply_markup=kb
    )
    await state.set_state(Rev.user_reply)


@router.message(F.text.lower(), Rev.user_reply)
async def finally_rating(message: Message, state: FSMContext):
    user_input = message.text.lower()
    if 'назад' in message.text.lower():
        kb = await state.get_value("rating_kb")
        await state.set_state(Rev.user_rating)
        await message.answer('Здравствуйте, выберите оценку:', reply_markup=kb)
        return

    if 'да' in user_input:
        msg_review = await sqlbase.execute_query('''SELECT review_message FROM settings_for_review_bot''')
        await message.answer(f'{msg_review[0][0]}', input_field_placeholder='Отзыв',
                             reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Rev.user_review)

    elif 'нет' in user_input:
        kb = await keyboard_factory.builder_reply_new_review()

        moscow_tz = timezone("Europe/Moscow")
        current_datetime = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
        chat_id = message.chat.id

        address = await state.get_value("user_address")
        place = await state.get_value("user_place")
        rating = await state.get_value("user_rating")

        await sqlbase.insert_in_reviews(current_datetime, address, place, str(chat_id), int(rating), )

        await message.answer('Спасибо за оценку нашего заведения!', reply_markup=kb)
        await sqlbase.close()

        await state.clear()

    else:
        kb = await state.get_value("choice_kb")

        await message.answer(
            "Можно ввести цифры или слова, которые есть в кнопках\nВведите, хотите ли вы написать отзыв",
            reply_markup=kb)


@router.message(Rev.user_review)
async def save_reviewer(message: Message, state: FSMContext):
    if message.text:
        kb = await keyboard_factory.builder_reply_new_review()

        moscow_tz = timezone("Europe/Moscow")
        current_datetime = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')

        chat_id = message.chat.id

        address = await state.get_value("user_address")
        place = await state.get_value("user_place")
        rating = await state.get_value("user_rating")
        review = message.text

        await sqlbase.insert_in_reviews(current_datetime, address, place, str(chat_id), int(rating), review=review)

        await message.answer('Спасибо за оценку нашего заведения!', reply_markup=kb)
        await sqlbase.close()

        await state.clear()

    else:
        await message.answer("Отзыв может содержать только символы")

    await sqlbase.close()
    await state.clear()
