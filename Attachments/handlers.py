from socketserver import DatagramRequestHandler

from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters.command import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from collections import OrderedDict

router = Router()
operator = '0'
rating = [1, 2, 3, 4, 5]

data = {}

# Определяем состояния для FSM
class Review(StatesGroup):
    user_id = State()
    user_rating = State()
    user_review = State()


# Обработчик команды /start с deep_link "one"
@router.message(CommandStart())#deep_link=True, magic=F.args == "one"))
async def reg_rating_one(message: Message, state: FSMContext):
    await state.set_state(Review.user_id)

    # Создаем клавиатуру для оценки
    builder = ReplyKeyboardBuilder()
    for i in range(1, 6):  # Оценки от 1 до 5
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(5)

    # Устанавливаем состояние "user_rating"
    await state.set_state(Review.user_rating)
    await message.answer('Поставьте оценку', reply_markup=builder.as_markup(resize_keyboard=True))


# Устанавливаем состояние "user_rating"


# Обработчик для получения оценки пользователя
@router.message(Review.user_rating)
async def too(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Review.user_review)
    await message.answer('Оценка принята')

# Обработчик для сохранения отзыва
@router.message(Review.user_review)
async def save_review(message: Message, state: FSMContext):


    await state.update_data(user_review=message.text)
    global data
    data = await state.get_data()

    data_revers = OrderedDict(data)
    data_revers['id_user'] = message.from_user.id
    data_revers.move_to_end('id_user', last=False)
    data_revers = dict(data_revers)
    # Выводим результат пользователю
    await message.answer(f'Спасибо за ваш отзыв! Оценка: {data_revers}')
    # Очищаем состояние
    await state.clear()


# Обработчик для ответа "Да" (написать отзыв)
