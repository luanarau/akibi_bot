from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
import bot as bot
import database as db


kb_buttons_start = [
    [
        KeyboardButton(text="начать ебашить"),
        KeyboardButton(text="посмотреть статистику")
    ],
]
keyboard_start = ReplyKeyboardMarkup(
    keyboard = kb_buttons_start,
    resize_keyboard = True,
    input_field_placeholder = ""
)

kb_statistics = [
        [KeyboardButton(text="Статистика за день")],
        [KeyboardButton(text="Статистика за неделю")],
        [KeyboardButton(text="Статистика за месяц")],
        [KeyboardButton(text="Назад")]
]
keyboard_statistics = ReplyKeyboardMarkup(keyboard = kb_statistics)


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
    ]
]

keyboard_pause = ReplyKeyboardMarkup(
    keyboard = kb_pause,
    resize_keyboard = True,
    input_field_placeholder = ""
)

kb_chose_reason = [[
        KeyboardButton(text="Без причины"),
]]

keyboard_chose_reason = ReplyKeyboardMarkup(
    keyboard = kb_chose_reason,
    resize_keyboard = True,
    input_field_placeholder = ""
)
