from sys import prefix
from typing import Union

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup


class InlineAddAdmin(CallbackData, prefix="AddAdmins"):
    action: str


class KeyboardFactory:

    def __init__(self):
        self.builder_reply = None

        self.builder_inline = None

    async def create_builder_reply(self) -> None:
        self.builder_reply = ReplyKeyboardBuilder()

    async def create_builder_inline(self) -> None:
        self.builder_inline = InlineKeyboardBuilder()

    async def builder_reply_choice(self, text_input: str) -> ReplyKeyboardMarkup:
        await self.create_builder_reply()
        self.builder_reply.add(KeyboardButton(text="Да✅"))
        self.builder_reply.add(KeyboardButton(text="Нет❌"))
        self.builder_reply.row(KeyboardButton(text="Назад"))
        keyboard = self.builder_reply.as_markup(
                                       resize_keyboard=True,
                                         input_field_placeholder=text_input, is_persistent =True)
        return keyboard

    async def builder_reply_text(self, texts: Union[tuple, list, set], input_field: str, cancel_button: bool) -> ReplyKeyboardMarkup:
        await self.create_builder_reply()

        for text in texts:
            self.builder_reply.add(KeyboardButton(text=text))

        if cancel_button:
            self.builder_reply.row(KeyboardButton(text="Назад"))

        first_keyboard = self.builder_reply.as_markup(resize_keyboard=True,
                                                      input_field_placeholder=input_field
                                                      , is_persistent=True)
        return first_keyboard

    async def builder_reply_cancel(self) -> ReplyKeyboardMarkup:
        await self.create_builder_reply()
        self.builder_reply.add(KeyboardButton(text='Отмена'))
        keyboard_cancel = self.builder_reply.as_markup(resize_keyboard=True,
                                                input_field_placeholder='Нажмите кнопку в случае необходимости')
        return keyboard_cancel

    async def builder_reply_rating(self) -> ReplyKeyboardMarkup:
        await self.create_builder_reply()
        for i in range(1, 6):
            self.builder_reply.add(KeyboardButton(text=str(i)))
        self.builder_reply.row(KeyboardButton(text="Назад"))

        first_keyboard = self.builder_reply.as_markup(resize_keyboard=True,
                                                      input_field_placeholder="Какую вы поставите оценку заведению?"
                                                      , is_persistent=True)
        return first_keyboard

    async def builder_reply_new_review(self):
        self.builder_reply.add(KeyboardButton(text="Отправить новый отзыв"))
        first_keyboard = self.builder_reply.as_markup(resize_keyboard=True,
                                                      input_field_placeholder="Какую вы поставите оценку заведению?"
                                                      , is_persistent=True)
        return first_keyboard

    async def builder_inline_add_admins(self):
        await self.create_builder_inline()

        add_button = InlineKeyboardButton(
            text="Принять",
            callback_data=InlineAddAdmin(
                action="accept",
            ).pack()
        )

        cancel_button = InlineKeyboardButton(
            text="Отклонить",
            callback_data=InlineAddAdmin(
                action="reject",
            ).pack()
        )

        self.builder_inline.add(add_button)
        self.builder_inline.row(cancel_button)

        return self.builder_inline.as_markup()

