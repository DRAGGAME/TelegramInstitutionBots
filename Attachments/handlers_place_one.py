import base64

from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters.command import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from collections import OrderedDict

from transliterate import translit

from config import ip, PG_user, PG_password, DATABASE
from datetime import datetime

from db.db_gino import Sqlbase


router = Router()
rating = ["1", '2', '3', '4', '5']
sqlbase = Sqlbase()

class Review(StatesGroup):
    user_id = State()
    user_place = State()
    user_rating = State()
    user_review = State()
# Определяем состояния для FSM
# Команда для администратора: показать все доступные ссылки
def transliterate_text(text):
    return translit(text, language_code='ru', reversed=True)



def encode_data(data):
    return base64.urlsafe_b64encode(data.encode()).decode()


# Функция декодирования для deep_link
def decode_data(payload):
    try:
        return base64.urlsafe_b64decode(payload.encode()).decode()
    except Exception:
        return None


# Генерация ссылки deep_link для места
async def generate_deep_link(place_name):
    transliterated_name = transliterate_text(place_name)  # Транслитерируем место
    encoded_place = encode_data(transliterated_name)  # Кодируем место
    bot_username = "deduwka_beerbox_bot"  # Укажи username своего бота
    return f"https://t.me/{bot_username}?start={encoded_place}"


# Обработчик команды /start с deep_link
@router.message(CommandStart(deep_link=True))
async def start_with_deep_link(message: Message, state: FSMContext):
    # Извлечение deep_link аргумента вручную из message.text
    if message.text and len(message.text.split()) > 1:
        encoded_arg = message.text.split()[1]  # Аргумент после /start
        place_name = decode_data(encoded_arg)  # Декодируем название места
        if place_name:
            await state.set_state(Review.user_place)
            place_name = translit(place_name, language_code='ru', reversed=True)
            await state.update_data(user_place=place_name)

            # Создаем клавиатуру для оценки
            builder = ReplyKeyboardBuilder()
            for i in range(1, 6):  # Оценки от 1 до 5
                builder.add(types.KeyboardButton(text=str(i)))
            builder.adjust(5)

            # Отправляем сообщение с просьбой оценить заведение
            await message.answer(
                f"Оцените, пожалуйста, наше заведение: {place_name}",
                reply_markup=builder.as_markup(resize_keyboard=True),
            )
            await state.set_state(Review.user_rating)
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
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        data = await state.get_data()
        await sqlbase.connect()

        data = OrderedDict(data)
        data['id_user'] = message.from_user.username
        await message.answer(f'Спасибо за оценку нашего заведения!', reply_markup=types.ReplyKeyboardRemove())

        await sqlbase.ins_ins(current_datetime, data['user_place'], data['id_user'],  int(data['user_rating']), 'Нет')

        await state.clear()


@router.message(Review.user_review)
async def save_review(message: Message, state: FSMContext):
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    await state.update_data(user_review=message.text)

    data = await state.get_data()
    await sqlbase.connect()
    data = OrderedDict(data)
    data['id_user'] = message.from_user.username
    await message.answer(f'Спасибо за оценку и отзыв нашего заведения!', reply_markup=types.ReplyKeyboardRemove())

    await sqlbase.ins_ins(current_datetime,
                        data['user_place'],
                        data['id_user'],
                        int(data['user_rating']),
                        data['user_review'])
    await state.clear()


@router.message(Review.user_rating, ~F.text.in_(rating))
async def too(message: Message):
    await message.reply('Можно ввести символы, только те, которые имеются на клавиатуре')


@router.message(Command(commands=["generate_links"]))
async def send_deep_links(message: Message):
    # Получаем список мест из базы
    await sqlbase.connect()
    places = await sqlbase.execute_query("SELECT place FROM message")
    places = [row[0] for row in places]

    # Генерируем ссылки для каждого места с транслитерацией
    links = []
    for place in places:
        deep_link = await generate_deep_link(place)
        links.append(f"{place}: {deep_link}")

    # Отправляем администратору список ссылок
    if links:
        link = await message.answer("\n\n".join(links))
    else:
        await message.answer("Нет доступных мест для генерации ссылок.")

