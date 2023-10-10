from aiogram import Bot, Dispatcher, types
from aiogram.filters import Filter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from functools import partial
from datetime import timedelta, datetime
import threading 
import youtrack_api as yt
import datetime
import database as db
import keyboard as kb
import asyncio
import logging
import sys


class Authorization(StatesGroup):
    tag = State()

    
class State_timer(StatesGroup):
    check_statistics = State()
    start_time = State()
    pause_reason = State()
    pause_start_time = State()
    end_time = State()
    



class MyFilter(Filter):
    def __init__(self, my_text: str) -> None:
        self.my_text = my_text

    async def __call__(self, message: Message) -> bool:
        return message.text == self.my_text


storage = MemoryStorage()

bot = Bot(token='6380806927:AAGZIZ_D7xl2b8hnS2_BP0KOyFCsyQIsr9M')
dp = Dispatcher(bot = bot, storage=storage)


# Запускает стартовое меню

@dp.message(MyFilter('/start'))
async def command_start_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("Салам!")
    if await db.authorize(message.from_user.id):
        await message.answer("У тебя нет учетной записи, но давай мы ее привяжем!\nВведи свой ник:")
        await state.set_state(Authorization.tag)
    else:
        await message.answer("Ты авторизован!", reply_markup = kb.keyboard_start)


# Autification State Machine        
#---------------------------------------------
    
    
@dp.message(Authorization.tag)
async def load_tag(message: types.Message, state: FSMContext) -> None:
    res = await db.insert_chat_id(message.from_user.id, message.text)
    if res:
        await message.reply("Тебя нет в youtracker, возможно ты неправильно ввел логин. Попробуй блять еще раз")
    else:
        await message.answer("Ты привязан!", reply_markup=kb.keyboard_start)
        await state.clear()
    

#-------------------------------------------

async def make_task_str(data: list) -> str:
    task_str = ''
    for task in data:
        task_str = task_str + (str)(task[0]) + ' task: ' + task[1]
        task_str = task_str + '\n'
    return task_str

# Начало отсчета времени

@dp.message(MyFilter('начать ебашить'))
async def start(message: types.Message, state: FSMContext):
    await state.update_data(start_time = datetime.datetime.now().time().replace(microsecond=0))
    await message.answer("Погнали нахуй!", reply_markup=kb.keyboard_end)
    await state.set_state(State_timer.start_time)


@dp.message(MyFilter('посмотреть статистику'))
async def start(message: types.Message, state: FSMContext):
    await message.answer("Какую статистику хочешь посмотреть?", reply_markup=kb.keyboard_statistics)
    await state.set_state(State_timer.check_statistics)
    
@dp.message(MyFilter('Статистика за день'), State_timer.check_statistics)
async def start(message: types.Message):
    data = await db.get_statistics_per_day(message.from_user.id)
    result = '\n'.join([f'День: {item[0]}, Время работы: {str(item[1])}' for item in data])
    await message.answer("Статистика за день:\n{}".format(result), reply_markup=kb.keyboard_statistics)
    

@dp.message(MyFilter('Статистика за неделю'), State_timer.check_statistics)
async def start(message: types.Message):
    data = await db.get_statistics_per_week(message.from_user.id)
    result = '\n'.join([f'День: {item[0]}, Время работы: {str(item[1])}' for item in data])
    await message.answer("Статистика за неделю:\n{}".format(result), reply_markup=kb.keyboard_statistics)
    
@dp.message(MyFilter('Статистика за месяц'), State_timer.check_statistics)
async def start(message: types.Message):
    data = await db.get_statistics_per_month(message.from_user.id)
    result = '\n'.join([f'День: {item[0]}, Время работы: {str(item[1])}' for item in data])
    await message.answer("Статистика за неделю:\n{}".format(result), reply_markup=kb.keyboard_statistics)
    
@dp.message(MyFilter('Назад'), State_timer.check_statistics)
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("ебашь сильнее...", reply_markup=kb.keyboard_start)
    
    
# Конец отсчета времени
 
@dp.message(MyFilter('закончить ебашить'), State_timer.start_time)
async def end(message: types.Message, state: FSMContext):
    await state.set_state(State_timer.end_time)
    await state.update_data(end_time = datetime.datetime.now().time().replace(microsecond=0))
    data = await state.get_data()
    time_difference = await delta_time(data)
    hours, seconds = divmod(time_difference.seconds, 3600)
    minutes = seconds // 60
    await message.answer("Ты работал {} часов и {} минут".format(hours, minutes), reply_markup=kb.keyboard_start)
    await state.set_state(State_timer.end_time)
    await db.insert_time_info(message.from_user.id, state, time_difference)
    await state.clear()
    
    
@dp.message(MyFilter('пауза'), State_timer.start_time)
async def set_pause(message: types.Message, state: FSMContext):
    await state.update_data(end_time = datetime.datetime.now().time().replace(microsecond=0))
    data = await state.get_data()
    time_difference = await delta_time(data)
    hours, seconds = divmod(time_difference.seconds, 3600)
    minutes = seconds // 60
    await message.answer("Ты работал {} часов и {} минут".format(hours, minutes))
    await message.answer('По какой причине уходишь? :(', reply_markup=kb.keyboard_chose_reason)
    await db.insert_time_info(message.from_user.id, state, time_difference)
    await state.set_state(State_timer.pause_reason)
    
    
@dp.message(State_timer.pause_reason)
async def pause_reason(message: types.Message, state: FSMContext):
    await state.update_data(pause_reason = message.text)
    await message.answer('Когда закончишь перерыв, нажми кнопку', reply_markup=kb.keyboard_pause)
    await state.update_data(pause_start_time = datetime.datetime.now().time().replace(microsecond=0))
    await state.set_state(State_timer.pause_start_time)
        

@dp.message(MyFilter('вернуться к работе'), State_timer.pause_start_time)
async def with_puree(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_date = datetime.date.today()
    start_time = datetime.datetime.combine(current_date, data['pause_start_time'])
    end_time = datetime.datetime.now().replace(microsecond=0)
    time_difference = end_time - start_time
    await db.insert_pause_time_info(message.from_user.id, state, time_difference)
    await state.set_state(State_timer.start_time)
    await state.update_data(start_time = datetime.datetime.now().time().replace(microsecond=0))
    await message.answer('продолжаем ебашить...', reply_markup=kb.keyboard_end)


async def delta_time(data: dict):
    current_date = datetime.date.today()
    start_datetime = datetime.datetime.combine(current_date, data['start_time'])
    end_datetime = datetime.datetime.combine(current_date, data['end_time'])
    time_difference = end_datetime - start_datetime
    return time_difference

    
async def main() -> None:
    bot = Bot(token='6380806927:AAGZIZ_D7xl2b8hnS2_BP0KOyFCsyQIsr9M')
    db.create_db()
    db.insert_developers()
    await dp.start_polling(bot)
 

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
    
    
    
    
