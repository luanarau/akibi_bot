from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import datetime
import bot as bot
import database as db


kb_buttons_start = [
        [KeyboardButton(text="начать ебашить")],
        [KeyboardButton(text="посмотреть статистику")],
        [KeyboardButton(text="изменить распиание")],
        [KeyboardButton(text="посмотреть расписание")]
]
keyboard_start = ReplyKeyboardMarkup(keyboard = kb_buttons_start)


kb_buttons_start_admin = [
        [KeyboardButton(text="начать ебашить")],
        [KeyboardButton(text="посмотреть статистику")],
        [KeyboardButton(text="изменить распиание")],
        [KeyboardButton(text="посмотреть расписание")],
        [KeyboardButton(text="активные разрабы")]
]
keyboard_start_admin = ReplyKeyboardMarkup(keyboard = kb_buttons_start_admin)


kb_buttons_before = [
        [KeyboardButton(text="назад")]
]
keyboard_before = ReplyKeyboardMarkup(
    keyboard = kb_buttons_before,
    resize_keyboard = True,
    input_field_placeholder = ""
)


kb_statistics = [
        [KeyboardButton(text="статистика за день")],
        [KeyboardButton(text="статистика за неделю")],
        [KeyboardButton(text="статистика за месяц")],
        [KeyboardButton(text="Назад")]
]
keyboard_statistics = ReplyKeyboardMarkup(keyboard = kb_statistics)

kb_statistics_admin = [
        [KeyboardButton(text="статистика за день")],
        [KeyboardButton(text="статистика за неделю")],
        [KeyboardButton(text="статистика за месяц")],
        [KeyboardButton(text="статистика разработчиков")],
        [KeyboardButton(text="Назад")]
]
keyboard_statistics_admin = ReplyKeyboardMarkup(keyboard = kb_statistics_admin)


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

kb_chose_time = [[
        KeyboardButton(text="8:00"),
        KeyboardButton(text="9:00"),
        KeyboardButton(text="10:00"),
        KeyboardButton(text="11:00"),
        KeyboardButton(text="12:00"),
]]

keyboard_chose_time = ReplyKeyboardMarkup(
    keyboard = kb_chose_time,
    resize_keyboard = True,
    input_field_placeholder = ""
)

kb_chose_admin = [[
        KeyboardButton(text="ес"),
        KeyboardButton(text="ноу"),
]]

keyboard_chose_admin = ReplyKeyboardMarkup(
    keyboard = kb_chose_admin,
    resize_keyboard = True,
    input_field_placeholder = ""
)

kb_chose_admin = [[
        KeyboardButton(text="ес"),
        KeyboardButton(text="ноу"),
]]

keyboard_chose_admin = ReplyKeyboardMarkup(
    keyboard = kb_chose_admin,
    resize_keyboard = True,
    input_field_placeholder = ""
)


def reply_builder():
    current_date = datetime.datetime.now()
    date_buttons_list = []
    day_list = []
    for i in range(7):
        button_day = []
        if (i == 6):
            day = 'Назад'
        else:
            current_date += datetime.timedelta(days=1)
            day = (str)(current_date.strftime("%d-%m"))
            day_list.append(day)
        button_day.append(KeyboardButton(text=day))
        date_buttons_list.append(button_day)
    return date_buttons_list, day_list

buttons_days_list, day_list = reply_builder()
keyboard_chose_day = ReplyKeyboardMarkup(keyboard=buttons_days_list)

def reply_builder_2():
    dev = db.get_dev()
    dev_list = []
    button_list = []
    back_list = []
    for login in dev:
        login_list = []
        dev_list.append(login[0])
        login_list.append(KeyboardButton(text = login[0]))
        button_list.append(login_list)
    back_list.append(KeyboardButton(text = 'Назад'))
    button_list.append(back_list)
    buttons_dev_list = button_list
    keyboard_chose_dev = ReplyKeyboardMarkup(keyboard=buttons_dev_list)
    return keyboard_chose_dev, dev_list




