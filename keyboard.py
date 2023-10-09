from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
import bot as bot
import database as db


kb_buttons_start = [
    [
        KeyboardButton(text="начать ебашить"),
    ],
]
keyboard_start = ReplyKeyboardMarkup(
    keyboard = kb_buttons_start,
    resize_keyboard = True,
    input_field_placeholder = ""
)


kb_buttons_end = [
    [
        KeyboardButton(text="закончить ебашить"),
        KeyboardButton(text="пауза")
    ],
]
keyboard_end = types.ReplyKeyboardMarkup(
    keyboard = kb_buttons_end,
    resize_keyboard = True,
    input_field_placeholder = ""
)

kb_pause = [
    [
        KeyboardButton(text="вернуться к работе"),
    ],
]
keyboard_pause = ReplyKeyboardMarkup(
    keyboard = kb_pause,
    resize_keyboard = True,
    input_field_placeholder = ""
)
