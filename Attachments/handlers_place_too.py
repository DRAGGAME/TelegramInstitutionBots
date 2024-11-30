from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters.command import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from collections import OrderedDict
import psycopg2
from db.db_gino import Sqlbase


from config import ip, PG_user, PG_password, DATABASE
from datetime import datetime

global data
router = Router()
operator = '0'
rating = ["1", '2', '3', '4', '5']
current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
sql_base = Sqlbase()
locales = ['Место один', 'Место три', 'Место два', 'Место четыре']

# Определяем состояния для FSM
class Rev(StatesGroup):
    user_id = State()
    user_place = State()
    user_rating = State()
    user_reply = State()
    user_review = State()


# Обработчик команды /start с deep_link "one"

@router.message(CommandStart())
async def starts(message: Message, state: FSMContext):
    kb = [
        [types.KeyboardButton(text='Место один')], [types.KeyboardButton(text='Место два')],
        [types.KeyboardButton(text='Место три')], [types.KeyboardButton(text='Место четыре')]
        ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder='Введите место')
    await message.answer('Выберите локацию', reply_markup=keyboard)
    await state.set_state(Rev.user_place)


@router.message(Rev.user_place, F.text.in_(locales))
async def reg_rating_one(message: Message, state: FSMContext):
    await state.update_data(user_place=message.text)
    # Создаем клавиатуру для оценки
    builder = ReplyKeyboardBuilder()
    for i in range(1, 6):  # Оценки от 1 до 5
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(5)
    # Устанавливаем состояние "user_rating"
    await message.answer('Поставьте оценку', reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(Rev.user_rating)

@router.message(Rev.user_rating, F.text.in_(rating))
async def too(message: Message, state: FSMContext):
    await state.update_data(user_rating=message.text)
    kb = [
        [types.KeyboardButton(text='Да'), types.KeyboardButton(text='Нет')],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder='Введите да или нет')
    await message.answer('Оценка принята\nЕсли вы желаете написать отзыв, то напишите "Да", если нет, то соответственно?', reply_markup=keyboard)


@router.message(F.text.in_(['Да','да','Нет','нет']), Rev.user_rating)
async def rat(message: Message, state: FSMContext):
    global data, data
    user_input = message.text

    if user_input in ['Да', 'да']:
        await message.answer('Напишите отзыв', input_field_placeholder='Напишите отзыв',reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Rev.user_review)

    elif user_input in ['Нет', 'нет']:
        data = await state.get_data()
        data = OrderedDict(data)
        data['id_user'] = message.from_user.id
        await message.answer(f'{data}' )
        sql_base.ins(current_datetime,
                     data['user_place'],
                     data['id_user'],
                     data['user_rating'],
                     None   )
        await state.clear()


# Обработчик для получения оценки пользователя


@router.message(Rev.user_review)
async def save_reviewer(message: Message, state: FSMContext):
    global data
    global data

    await state.update_data(user_review=message.text)
    data = await state.get_data()
    data = OrderedDict(data)
    data['id_user'] = message.from_user.id


    await message.answer(f'{data}')

    sql_base.ins(current_datetime,
                 data['user_place'],
                 data['id_user'],
                 data['user_rating'],
                 data['user_review'])


@router.message(Rev.user_rating, ~F.text.in_(rating))
async def too(message: Message):
    await message.reply('Можно ввести символы, только те, которые имеются на клавиатуре')

@router.message(Rev.user_place, ~F.text.in_(locales))
async def too(message: Message):
    await message.reply('Можно ввести символы, только те, которые имеются на клавиатуре')