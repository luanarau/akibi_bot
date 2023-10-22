from aiogram import Bot, Dispatcher, types
from aiogram.filters import Filter
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import Message, InputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from datetime import timedelta, datetime
from dotenv import load_dotenv
import datetime
import database as db
import keyboard as kb
import stickers
import asyncio
import logging
import os
import sys

load_dotenv()

## Основная машина состояний

class State_timer(StatesGroup):
    
    ## Состояния для регистрации пользователя
    tag = State()
    admin = State()
    admin_token = State()
    
    ## Состояния начала работы бота (start_bot) и просмотра статистики
    start_bot = State()
    check_statistics_on_shift = State()
    check_statistics_not_on_shift = State()
    solo_dev = State()
    
    ## Состояния таймера пользователя
    start_time = State()
    pause_reason = State()
    pause_start_time = State()
    end_time = State()
    
    ## Состояния выхода из просмотра статистики когда таймер включен/когда таймер выключен
    back_on_shift = State()
    back_not_on_shift = State()
    
    ## Состояние выбора графика когда таймер включен/когда таймер выключен
    chose_day_on_shift = State()
    chose_day_not_on_shift = State()
    chose_time_on_shift = State()
    chose_time_not_on_shift = State()
    
    
 ## Машина состояний при удалении учетной записи   
 
class State_remove_acc(StatesGroup):
    remove = State()


## Класс для удобной обработки текста отправляемого пользователем

class MyFilter(Filter):
    def __init__(self, my_text: str) -> None:
        self.my_text = my_text

    async def __call__(self, message: Message) -> bool:
        return message.text == self.my_text

## Функция для отправки сообщений (Нужна для scheduler) и рандомного стикера

async def print_sheduler_message(message: types.Message, text):
    await message.answer(text)
    await message.answer_sticker(stickers.get_random_cat())

## Schedulers

scheduler_2_hours = AsyncIOScheduler()
scheduler_15_min = AsyncIOScheduler()
scheduler_before_shift = AsyncIOScheduler()
scheduler_after_shift = AsyncIOScheduler()
check_next_day = AsyncIOScheduler()
zero_impact = AsyncIOScheduler()


bot_token = os.getenv('BOT_TOKEN')
admin_token = os.getenv('ADMIN_TOKEN')
bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot = bot, storage=storage)


# Запускает стартовое меню и авторизацию

@dp.message(MyFilter('/start'))
async def command_start_handler(message: types.Message, state: FSMContext) -> None:
    await db.change_is_active(False, message.chat.id)
    zero_impact.add_job(db.insert_zero, 'cron', hour=23, minute=59, args=[message.chat.id])
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZk5lJnMTnPjXYKzHP88a_sRguf_0OAAC1xgAAm4m4UsFYy3CmOv8qzAE')
    if await db.authorize(message.from_user.id):
        await message.answer("У тебя нет учетной записи, но давай мы ее привяжем!\nВведи свой ник из youtracker'а:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(State_timer.tag)
    else:
        if not await db.is_admin(message.chat.id):
            keyboard = kb.keyboard_start
        else:
            keyboard = kb.keyboard_start_admin
        await message.answer("Ты авторизован!", reply_markup = keyboard)
        await state.set_state(State_timer.start_bot)
            

@dp.message(State_timer.tag)
async def load_tag(message: types.Message, state: FSMContext) -> None:
    res = await db.insert_chat_id(message.from_user.id, message.text)
    if res:
        await message.reply("Тебя нет в youtracker, возможно ты неправильно ввел логин. Попробуй блять еще раз")
    else:
        await message.answer("Логин привязан", reply_markup=ReplyKeyboardRemove())
        await message.answer("Давай второй вопрос: Ты админ?", reply_markup=kb.keyboard_chose_admin)
        await state.set_state(State_timer.admin)
        

@dp.message(State_timer.admin)
async def load_tag(message: types.Message, state: FSMContext) -> None:
    if (message.text == 'да'):
        await state.set_state(State_timer.admin_token)
        await message.answer("Введи свой токен:", reply_markup=kb.keyboard_before)
    elif (message.text == 'нет'):   
        await message.answer('Все супер, можешь спокойно работать', reply_markup=kb.keyboard_start)
        await state.set_state(State_timer.start_bot)
    else:
        await message.answer('Для кого кнопки придуманы, друг?')

@dp.message(State_timer.admin_token)
async def load_tag(message: types.Message, state: FSMContext) -> None:
    if message.text == admin_token:
        await message.answer("Поздравляю, теперь ты админ", reply_markup=kb.keyboard_start_admin)
        await state.set_state(State_timer.start_bot)
        await db.grant_admin(message.chat.id)
    elif message.text == 'назад':
        await message.answer("Давай второй вопрос: Ты админ?", reply_markup=kb.keyboard_chose_admin)
        await state.set_state(State_timer.admin)
    else:
        await message.answer("неправильный токен :(", kb.keyboard_before)

 
## Функции работающие с расписанием (Зависит от того вошел он в них во время смены или нет)

@dp.message(MyFilter('изменить распиание'), State_timer.start_time)
async def start(message: types.Message, state: FSMContext):
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZsllJoVjc3n5KjTTrE_SdQxgZ2RNcQACKBYAAi8x4UvsAnm5hTjEHTAE')
    await state.set_state(State_timer.chose_day_on_shift)
    await message.answer("Выбери день:", reply_markup=kb.keyboard_chose_day)
    
@dp.message(MyFilter('изменить распиание'), State_timer.start_bot)
async def start(message: types.Message, state: FSMContext):
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZsllJoVjc3n5KjTTrE_SdQxgZ2RNcQACKBYAAi8x4UvsAnm5hTjEHTAE')
    await state.set_state(State_timer.chose_day_not_on_shift)
    await message.answer("Выбери день:", reply_markup=kb.keyboard_chose_day)

    
@dp.message(State_timer.chose_day_on_shift)
async def chose_day_on_shift(message: types.Message, state: FSMContext):
    await choose_day(message, state, True)
        
@dp.message(State_timer.chose_day_not_on_shift)
async def chose_day_not_on_shift(message: types.Message, state: FSMContext):
    await choose_day(message, state, False)

async def choose_day(message: types.Message, state: FSMContext, on_shift: bool):
    date = message.text
    date_buttons_list, day_list = kb.reply_builder()
    if date in day_list:
        day, month = date.split("-")
        current_year = datetime.datetime.now().year
        await state.update_data(chose_day = f"{current_year}-{month}-{day}")
        await message.answer("Выбери время начала смены:", reply_markup=kb.keyboard_chose_time)
        await state.set_state(State_timer.chose_time_on_shift) if on_shift else await state.set_state(State_timer.chose_time_not_on_shift)
    elif (date == 'Назад'):
        keyboard = kb.keyboard_start if not await db.is_admin(message.chat.id) else kb.keyboard_start_admin
        await message.answer("Возвращайся когда захочешь изменить свое расписание", reply_markup = keyboard)
        await message.answer_sticker(r'CAACAgIAAxkBAAEBbPJlJ6i7YmB2Ie-1ifw1aHRxanx2qgACRRoAAphU0Ep9f9XploWBYDAE')
        await state.set_state(State_timer.start_time) if on_shift else await state.set_state(State_timer.start_bot)
    else:
        await message.answer_sticker(r'CAACAgIAAxkBAAEBbNJlJ6IDTcw9lnZ9b8TCU0LMVg-deQACHgADaudPF-sCqDIPF6zoMAQ')
        await message.answer("Для кого кнопки придуманы, друг?")
    

@dp.message(State_timer.chose_time_on_shift)
async def chose_time_on_shift(message: types.Message, state: FSMContext):
    await choose_time(message, state, True)

@dp.message(State_timer.chose_time_not_on_shift)
async def chose_time_not_on_shift(message: types.Message, state: FSMContext):
    await choose_time(message, state, False)
        
async def choose_time(message: types.Message, state: FSMContext, on_shift: bool):
    time = message.text
    time_list = ["8:00", "9:00", "10:00", "11:00", "12:00"]
    if time in time_list:
        await state.update_data(chose_time = time)
        start_time = datetime.datetime.strptime(time, '%H:%M')
        end_time = start_time + timedelta(hours=8)
        formatted_time = end_time.strftime('%H:%M')
        await db.insert_dev_schedule(message, message.chat.id, state, formatted_time)
        await message.answer("Время изменено. Смена закончится в: {}".format(formatted_time), reply_markup=kb.keyboard_chose_day)
        await state.set_state(State_timer.chose_day_on_shift) if on_shift else await state.set_state(State_timer.chose_day_not_on_shift)
    else:
        await message.answer_sticker(r'CAACAgIAAxkBAAEBbNJlJ6IDTcw9lnZ9b8TCU0LMVg-deQACHgADaudPF-sCqDIPF6zoMAQ')
        await message.answer("Для кого кнопки придуманы, друг?")
    
@dp.message(MyFilter('посмотреть расписание'))
async def chose_day(message: types.Message, state: FSMContext):
    data = await db.get_full_schedule(message.chat.id)
    if data:
        result = '\n'.join([f'{item[0]}: Начало: {str(item[1])}, Конец: {str(item[2])}' for item in data])
    else:
        result = 'Пока ничего нет'
    await message.answer("Расписание на ближайшую неделю:\n{}".format(result))


## Функции работающие со статистикой (Зависит от того вошел он в них во время смены или нет)

@dp.message(MyFilter('посмотреть статистику'))
async def start(message: types.Message, state: FSMContext):
    keyboard = kb.keyboard_statistics_admin if await db.is_admin(message.chat.id) else kb.keyboard_statistics
    await message.answer("Какую статистику хочешь посмотреть?", reply_markup=keyboard)

  
@dp.message(MyFilter('статистика за день'))
async def start(message: types.Message):
    data = await db.get_statistics_per_day(message.from_user.id)
    result = '\n'.join([f'День: {item[0]}, Время работы: {str(item[1])}' for item in data]) if data else 'Пока ничего нет'
    await message.answer("Статистика за день:\n{}".format(result))
    

@dp.message(MyFilter('статистика за неделю'))
async def start(message: types.Message):
    data = await db.get_statistics_per_week(message.from_user.id)
    if data:
        result = '\n'.join([f'День: {item[0]}, Время работы: {str(item[1])}' for item in data])
        await db.productivity_solo_week(message)
    else:
        result = 'Пока ничего нет'
    await message.answer("Статистика за неделю:\n{}".format(result))

   
@dp.message(MyFilter('статистика за месяц'))
async def start(message: types.Message):
    data = await db.get_statistics_per_month(message.from_user.id)
    if data:
        result = '\n'.join([f'День: {item[0]}, Время работы: {str(item[1])}' for item in data])
        await db.productivity_solo_month(message)
    else:
        result = 'Пока ничего нет'
    await message.answer("Статистика за месяц:\n{}".format(result))


@dp.message(MyFilter('статистика разработчиков'), State_timer.start_bot)
async def dev_statistics_not_on_shift(message: types.Message, state: FSMContext):
    await dev_statistics(message, state, False)
        
@dp.message(MyFilter('статистика разработчиков'), State_timer.start_time)
async def dev_statistics_on_shift(message: types.Message, state: FSMContext):
    await dev_statistics(message, state, True)
    
async def dev_statistics(message: types.Message, state: FSMContext, on_shift: bool):
    dev_statistics_work, dev_statistics_chill, dev_chill_reasons = await db.get_dev_statistics_to_admin()
    top_3_workers = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_statistics_work]) if dev_statistics_work else 'Пока ничего нет'
    top_3_chillers = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_statistics_chill]) if dev_statistics_chill else 'Пока ничего нет'
    top_3_chill_reasons = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_chill_reasons]) if dev_chill_reasons else 'Пока ничего нет'
    text_if_no_dev = ':)' if db.get_dev() else '(У тебя нет работников, нано)'
    keyboard, dev = kb.reply_builder_2()
    await message.answer("Топ 3 работника (по рабочему времени):\n{}\n\nТоп 3 прогульщика (по времени отдыха):\n{}\n\nТоп 3 причины отдыха:\n{}\n\nЕсли хочешь увидеть статистику кого-нибудь определенного нажми на кнопку {}".format(top_3_workers, top_3_chillers, top_3_chill_reasons, text_if_no_dev), reply_markup=keyboard)
    await db.productivity_all_dev(message)
    await state.set_state(State_timer.check_statistics_on_shift) if on_shift else await state.set_state(State_timer.check_statistics_not_on_shift)


@dp.message(State_timer.check_statistics_on_shift)
async def solo_dev_statistics_on_shift(message: types.Message, state: FSMContext):
    await solo_dev_statistics(message, state)
        
@dp.message(State_timer.check_statistics_not_on_shift)
async def solo_dev_statistics_on_shift(message: types.Message, state: FSMContext):
    await solo_dev_statistics(message, state)
        
async def solo_dev_statistics(message: types.Message, state: FSMContext, on_shift: bool):
    keyboard, dev = kb.reply_builder_2()
    if message.text in dev and await db.is_admin(message.chat.id):
        dev_statistics_work, dev_statistics_chill, dev_chill_reasons = await db.get_dev_statistics_to_solo_dev(message.text)
        top_3_workers = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_statistics_work]) if dev_statistics_work else 'Пока ничего нет'
        top_3_chillers = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_statistics_chill]) if dev_statistics_chill else 'Пока ничего нет'
        top_3_chill_reasons = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_chill_reasons]) if dev_chill_reasons else 'Пока ничего нет'
        await message.answer("Смены за последнюю неделю:\n{}\n\nПерерывы за последнюю неделю:\n{}\n\nТоп 3 причины отдыха:\n{}\n".format(top_3_workers, top_3_chillers, top_3_chill_reasons), reply_markup=keyboard)
        await db.productivity_solo(message, message.text)
    elif message.text == 'Назад':
        await back_on_shift(message, state) if on_shift else await back_not_on_shift(message, state)
    
        
## Отправляет сообщение с разработчиками и статусом (Работает/Не работает)

@dp.message(MyFilter('активные разрабы'))
async def check_active_dev(message: types.Message):
    if await db.is_admin(message.chat.id):
        is_active = await db.get_is_active()
        result = '\n'.join([f'{item[0]}: {"Работает" if item[1] else "Отдыхает"}' for item in is_active])
        await message.answer(result)


## Различные условия выхода, при нажатии на кнопку 'Назад'

@dp.message(MyFilter('Назад'), State_timer.start_time)
async def back(message: types.Message):
    await send_if_back_statistics(message, True)
    
@dp.message(MyFilter('Назад'), State_timer.start_bot)
async def back(message: types.Message):
    await send_if_back_statistics(message, False)

async def back_on_shift(message: types.Message, state: FSMContext):
    await send_if_back_statistics(message, True)
    await state.set_state(State_timer.start_time)
    
async def back_not_on_shift(message: types.Message, state: FSMContext):
    await send_if_back_statistics(message, True)
    await state.set_state(State_timer.start_bot)


async def send_if_back_statistics(message: types.Message, on_shift: bool):
    if on_shift:
        keyboard = kb.keyboard_end
        keyboard_admin = kb.keyboard_end_admin
    else:
        keyboard = kb.keyboard_start
        keyboard_admin = kb.keyboard_start_admin 
    await message.answer("Возвращйся когда захочешь посмотреть статистику", reply_markup=keyboard_admin) if await db.is_admin(message.chat.id) else await message.answer("Возвращйся когда захочешь посмотреть статистику", reply_markup=keyboard)
    await message.answer_sticker(r'CAACAgIAAxkBAAEBj_9lNPhtisfYFpWr0Jsi_r2q9BQOyQAC9BcAAop8IEgmgbl30zIBnTAE')


## Основные функции работы с таймером: Начать/Закончить/Поставить на паузу

@dp.message(MyFilter('начать смену'), State_timer.start_bot)
async def start_shift(message: types.Message, state: FSMContext): 
    if not await db.is_admin(message.chat.id):
        keyboard = kb.keyboard_end
        await info_dev(message, 'начал работу')
    else:
        keyboard = kb.keyboard_end_admin
    await state.update_data(start_time = datetime.datetime.now().time().replace(microsecond=0))
    await message.answer("Смена началась!", reply_markup=keyboard)
    scheduler_2_hours.add_job(print_sheduler_message, trigger='interval', minutes=120, args=[message, "Ты ебашил 2 часа, может пора сделать перерыв?"], id='2_hours_{}'.format(message.chat.id))
    await db.change_is_active(True, message.chat.id)
    await state.set_state(State_timer.start_time)


@dp.message(MyFilter('закончить смену'), State_timer.start_time)
async def end_shift(message: types.Message, state: FSMContext):
    if not await db.is_admin(message.chat.id):
        keyboard = kb.keyboard_start
    else:
        keyboard = kb.keyboard_start_admin
    await info_dev(message, 'закончил работать')
    await state.update_data(end_time = datetime.datetime.now().time().replace(microsecond=0))
    scheduler_2_hours.remove_job(job_id='2_hours_{}'.format(message.chat.id))
    data = await state.get_data()
    time_difference = await delta_time(data)
    hours, seconds = divmod(time_difference.seconds, 3600)
    minutes = seconds // 60
    await message.answer("Ты работал {} часов и {} минут".format(hours, minutes))
    await message.answer("Надеюсь ты хорошо провел время и сделал хоть что то полезное :)", reply_markup=keyboard)
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZghlJmTe3n1WMsBEqiQocf_rW2ggtQACfwkAAibJ6UiBeQ1qzGbWLTAE')
    await state.set_state(State_timer.start_bot)
    await db.insert_time_info(message.from_user.id, state, time_difference)
    await db.change_is_active(False, message.chat.id)
    
@dp.message(MyFilter('пауза'), State_timer.start_time)
async def set_pause(message: types.Message, state: FSMContext):
    await state.update_data(end_time = datetime.datetime.now().time().replace(microsecond=0))
    await db.change_is_active(False, message.chat.id)
    scheduler_2_hours.shutdown(wait=False)
    scheduler_2_hours.remove_job(job_id='2_hours_{}'.format(message.chat.id))
    scheduler_15_min.add_job(print_sheduler_message, trigger='interval', minutes=15, args=[message, "Ты отдыхаешь слишком долго..."], id='15_minutes_{}'.format(message.chat.id))
    data = await state.get_data()
    time_difference = await delta_time(data)
    hours, seconds = divmod(time_difference.seconds, 3600)
    minutes = seconds // 60
    await message.answer("Ты работал {} часов и {} минут".format(hours, minutes))
    await message.answer('По какой причине уходишь? :(', reply_markup=kb.keyboard_chose_reason)
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZjplJnCFpRHsiYy2OPYAAX5apgNjz38AAkkSAAI_6iBIQj0t_B52J9MwBA')
    await db.insert_time_info(message.from_user.id, state, time_difference)
    await state.set_state(State_timer.pause_reason)
    
@dp.message(State_timer.pause_reason)
async def pause_reason(message: types.Message, state: FSMContext):
    await state.update_data(pause_reason = message.text)
    await message.answer('Когда закончишь перерыв, нажми кнопку', reply_markup=kb.keyboard_pause)
    await state.update_data(pause_start_time = datetime.datetime.now().time().replace(microsecond=0))
    await state.set_state(State_timer.pause_start_time)
        
@dp.message(MyFilter('вернуться к работе'), State_timer.pause_start_time)
async def back_to_work(message: types.Message, state: FSMContext):
    await db.change_is_active(True, message.chat.id)
    keyboard = kb.keyboard_end_admin if await db.is_admin(message.chat.id) else kb.keyboard_end
    scheduler_2_hours.add_job(print_sheduler_message, trigger='interval', minutes=120, args=[message, "Ты ебашил 2 часа, может пора сделать перерыв?"], id='2_hours_{}'.format(message.chat.id))
    scheduler_15_min.remove_job(job_id='15_minutes_{}'.format(message.chat.id))
    data = await state.get_data()
    current_date = datetime.date.today()
    start_time = datetime.datetime.combine(current_date, data['pause_start_time'])
    end_time = datetime.datetime.now().replace(microsecond=0)
    time_difference = end_time - start_time
    await db.insert_pause_time_info(message.from_user.id, state, time_difference)
    await state.set_state(State_timer.start_time)
    await state.update_data(start_time = datetime.datetime.now().time().replace(microsecond=0))
    await message.answer('продолжаем работать...', reply_markup=keyboard)
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZgZlJmQfGnQaKD1B9A82EEDVfl_yQwACNRQAAkN2IUhAgVSjcyNt0TAE')
    
## Считает и возвращает время для отправки сообщением

async def delta_time(data: dict):
    current_date = datetime.date.today()
    start_datetime = datetime.datetime.combine(current_date, data['start_time'])
    end_datetime = datetime.datetime.combine(current_date, data['end_time'])
    time_difference = end_datetime - start_datetime
    return time_difference
    
## Рассылает админам уведомление о начале работы какого-либо разработчика

async def info_dev(message: types.Message, text: str):
    admins = await db.all_admins()
    my_login = await db.get_my_login(message.chat.id)
    for data in admins:
        if data[0]:
            if (int)(data[0]) != message.chat.id:
                await bot.send_message(chat_id=(int)(data[0]), text='{} {}'.format(my_login[0], text))
                
                
## Функции сбрасывающие учетную запись
 
@dp.message(MyFilter('сброс учетки'))
async def remove_acc(message: types.Message, state: FSMContext):
    await message.answer("Ты уверен?", reply_markup=kb.keyboard_chose_admin)
    await state.set_state(State_remove_acc.remove)   
 
@dp.message(State_remove_acc.remove)
async def remove_acc(message: types.Message, state: FSMContext):
    if message.text == 'да':
        await db.remove_acc(message.chat.id)
        await message.answer("Окей пока! Если хочешь опять начать напиши /start", reply_markup=ReplyKeyboardRemove())
        await message.answer_sticker(r'CAACAgIAAxkBAAEBbPJlJ6i7YmB2Ie-1ifw1aHRxanx2qgACRRoAAphU0Ep9f9XploWBYDAE')
        await state.clear()
    elif message.text == 'нет':
        if not await db.is_admin(message.chat.id):
            keyboard = kb.keyboard_start
        else:
            keyboard = kb.keyboard_start_admin
        await message.answer("ну и ладно...", reply_markup=keyboard)
        await state.clear()
    else:
        await message.answer("давай еше раз, тебе сбросить учетку?", reply_markup=kb.keyboard_chose_admin)
        await message.answer_sticker(r'CAACAgIAAxkBAAEBgVZlL3tszdN_P9VhMQOw6M6qwuhWswACPxMAAtlwOEpSw_r2yt988jAE')
        


async def main() -> None:
    db.create_db()
    db.insert_developers()
    scheduler_2_hours.start()
    scheduler_15_min.start()
    scheduler_before_shift.start()
    scheduler_after_shift.start()
    zero_impact.start()
    await dp.start_polling(bot)
 

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
    
    
    
    
