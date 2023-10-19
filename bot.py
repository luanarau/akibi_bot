from aiogram import Bot, Dispatcher, types
from aiogram.filters import Filter
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from datetime import timedelta, datetime
import datetime
import database as db
import keyboard as kb
import stickers
import asyncio
import logging
import sys


class Authorization(StatesGroup):
    tag = State()
    admin = State()
    admin_token = State()

    
class State_timer(StatesGroup):
    check_statistics = State()
    solo_dev = State()
    start_time = State()
    pause_reason = State()
    pause_start_time = State()
    end_time = State()
    
class State_choose_schedule(StatesGroup):
    chose_day = State()
    chose_time = State()



class MyFilter(Filter):
    def __init__(self, my_text: str) -> None:
        self.my_text = my_text

    async def __call__(self, message: Message) -> bool:
        return message.text == self.my_text


async def print_sheduler_message(message: types.Message, text):
    await message.answer(text)
    await message.answer_sticker(stickers.get_random_cat())


storage = MemoryStorage()
scheduler_2_hours = AsyncIOScheduler()
scheduler_15_min = AsyncIOScheduler()
scheduler_before_shift = AsyncIOScheduler()
scheduler_after_shift = AsyncIOScheduler()
check_next_day = AsyncIOScheduler()

bot = Bot(token='6980384013:AAEIE5qvjHjbNMtSXsFZKdnDVdpnNrSA44I')
dp = Dispatcher(bot = bot, storage=storage)
admin_token = 'hui'


# Запускает стартовое меню

@dp.message(MyFilter('/start'))
async def command_start_handler(message: types.Message, state: FSMContext) -> None:
    await db.change_is_active(False, message.chat.id)
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZk5lJnMTnPjXYKzHP88a_sRguf_0OAAC1xgAAm4m4UsFYy3CmOv8qzAE')
    if await db.authorize(message.from_user.id):
        await message.answer("У тебя нет учетной записи, но давай мы ее привяжем!\nВведи свой ник из youtracker'а:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Authorization.tag)
    else:
        if not await db.is_admin(message.chat.id):
            await message.answer("Ты авторизован!", reply_markup = kb.keyboard_start)
        else:
            await message.answer("Ты авторизован!", reply_markup = kb.keyboard_start_admin)
            
            
@dp.message(Authorization.tag)
async def load_tag(message: types.Message, state: FSMContext) -> None:
    res = await db.insert_chat_id(message.from_user.id, message.text)
    if res:
        await message.reply("Тебя нет в youtracker, возможно ты неправильно ввел логин. Попробуй блять еще раз")
    else:
        await message.answer("Логин привязан", reply_markup=ReplyKeyboardRemove())
        await message.answer("Давай второй вопрос: Ты админ?", reply_markup=kb.keyboard_chose_admin)
        await state.set_state(Authorization.admin)
        

@dp.message(Authorization.admin)
async def load_tag(message: types.Message, state: FSMContext) -> None:
    if (message.text == 'ес'):
        await state.set_state(Authorization.admin_token)
        await message.answer("Введи свой токен:", reply_markup=kb.keyboard_before)
    elif (message.text == 'ноу'):   
        await message.answer('Все супер, можешь спокойно ебашить', reply_markup=kb.keyboard_start)
        await state.clear()
    else:
        await message.answer('Для кого кнопки придуманы, долбоеб?')

@dp.message(Authorization.admin_token)
async def load_tag(message: types.Message, state: FSMContext) -> None:
    if message.text == admin_token:
        await message.answer("Заебись, теперь ты руководишь этим цирком", reply_markup=kb.keyboard_start_admin)
        await db.grant_admin(message.chat.id)
        await state.clear()
    elif message.text == 'назад':
        await message.answer("Давай второй вопрос: Ты админ?", reply_markup=kb.keyboard_chose_admin)
        await state.set_state(Authorization.admin)
    else:
        await message.answer("Ввел хуйню какую-то, попробуй еще раз", kb.keyboard_before)
    
    
@dp.message(MyFilter('изменить распиание'))
async def start(message: types.Message, state: FSMContext):
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZsllJoVjc3n5KjTTrE_SdQxgZ2RNcQACKBYAAi8x4UvsAnm5hTjEHTAE')
    await state.set_state(State_choose_schedule.chose_day)
    await message.answer("Выбери день:", reply_markup=kb.keyboard_chose_day)

    
@dp.message(State_choose_schedule.chose_day)
async def chose_day(message: types.Message, state: FSMContext):
    date = message.text
    date_buttons_list, day_list = kb.reply_builder()
    if date in day_list:
        day, month = date.split("-")
        current_year = datetime.datetime.now().year
        await state.update_data(chose_day = f"{current_year}-{month}-{day}")
        await message.answer("Выбери время начала смены:", reply_markup=kb.keyboard_chose_time)
        await state.set_state(State_choose_schedule.chose_time)
    elif (date == 'Назад'):
        await state.clear()
        if not await db.is_admin(message.chat.id):
            await message.answer("Возвращайся когда захочешь изменить свое расписание", reply_markup = kb.keyboard_start)
        else:
            await message.answer("Возвращайся когда захочешь изменить свое расписание", reply_markup = kb.keyboard_start_admin)
        await message.answer_sticker(r'CAACAgIAAxkBAAEBbPJlJ6i7YmB2Ie-1ifw1aHRxanx2qgACRRoAAphU0Ep9f9XploWBYDAE')
    else:
        await message.answer_sticker(r'CAACAgIAAxkBAAEBbNJlJ6IDTcw9lnZ9b8TCU0LMVg-deQACHgADaudPF-sCqDIPF6zoMAQ')
        await message.answer("Для кого кнопки придуманы, долбаеб?")


@dp.message(MyFilter('посмотреть расписание'))
async def chose_day(message: types.Message, state: FSMContext):
    data = await db.get_full_schedule(message.chat.id)
    if data:
        result = '\n'.join([f'{item[0]}: Начало: {str(item[1])}, Конец: {str(item[2])}' for item in data])
    else:
        result = 'Пока ничего нет'
    await message.answer("Расписание на ближайшую неделю:\n{}".format(result))
    

@dp.message(State_choose_schedule.chose_time)
async def chose_time(message: types.Message, state: FSMContext):
    time = message.text
    time_list = ["8:00", "9:00", "10:00", "11:00", "12:00"]
    if time in time_list:
        await state.update_data(chose_time = time)
        start_time = datetime.datetime.strptime(time, '%H:%M')
        end_time = start_time + timedelta(hours=8)
        formatted_time = end_time.strftime('%H:%M')
        await db.insert_dev_schedule(message, message.chat.id, state, formatted_time)
        await message.answer("Время изменено. Смена закончится в: {}".format(formatted_time), reply_markup=kb.keyboard_chose_day)
        await state.set_state(State_choose_schedule.chose_day)
    else:
        await message.answer_sticker(r'CAACAgIAAxkBAAEBbNJlJ6IDTcw9lnZ9b8TCU0LMVg-deQACHgADaudPF-sCqDIPF6zoMAQ')
        await message.answer("Для кого кнопки придуманы, долбаеб?")


@dp.message(MyFilter('посмотреть статистику'))
async def start(message: types.Message, state: FSMContext):
    if not await db.is_admin(message.chat.id):
        await message.answer("Какую статистику хочешь посмотреть?", reply_markup=kb.keyboard_statistics)
    else:
        await message.answer("Какую статистику хочешь посмотреть?", reply_markup=kb.keyboard_statistics_admin)
    await state.set_state(State_timer.check_statistics)

  
@dp.message(MyFilter('статистика за день'), State_timer.check_statistics)
async def start(message: types.Message):
    data = await db.get_statistics_per_day(message.from_user.id)
    if data:
        result = '\n'.join([f'День: {item[0]}, Время работы: {str(item[1])}' for item in data])
    else:
        result = 'Пока ничего нет'
    await message.answer("Статистика за день:\n{}".format(result), reply_markup=kb.keyboard_statistics)
    

@dp.message(MyFilter('статистика за неделю'), State_timer.check_statistics)
async def start(message: types.Message):
    data = await db.get_statistics_per_week(message.from_user.id)
    if data:
        result = '\n'.join([f'День: {item[0]}, Время работы: {str(item[1])}' for item in data])
    else:
        result = 'Пока ничего нет'
    await message.answer("Статистика за неделю:\n{}".format(result), reply_markup=kb.keyboard_statistics)

   
@dp.message(MyFilter('статистика за месяц'), State_timer.check_statistics)
async def start(message: types.Message):
    data = await db.get_statistics_per_month(message.from_user.id)
    if data:
        result = '\n'.join([f'День: {item[0]}, Время работы: {str(item[1])}' for item in data])
    else:
        result = 'Пока ничего нет'
    await message.answer("Статистика за месяц:\n{}".format(result), reply_markup=kb.keyboard_statistics)


@dp.message(MyFilter('статистика разработчиков'), State_timer.check_statistics)
async def dev_statistics(message: types.Message, state: FSMContext):
    dev_statistics_work, dev_statistics_chill, dev_chill_reasons = await db.get_dev_statistics_to_admin()
    if dev_statistics_work:
        top_3_workers = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_statistics_work])
    else:
        top_3_workers = 'Пока ничего нет'
    if dev_statistics_chill:
        top_3_chillers = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_statistics_chill])
    else:
        top_3_chillers = 'Пока ничего нет'
    if dev_chill_reasons:
        top_3_chill_reasons = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_chill_reasons])
    else:
        top_3_chill_reasons = 'Пока ничего нет'
    if not db.get_dev():
        text_if_no_dev = '(У тебя нет работников, нано)'
    else: 
        text_if_no_dev = ':)'
    keyboard, dev = kb.reply_builder_2()
    await message.answer("Топ 3 работника этого цирка:\n{}\n\nТоп 3 прогульщика этого цирка:\n{}\n\nТоп 3 причины отдыха:\n{}\n\nЕсли хочешь увидеть статистику кого-нибудь определенного нажми на кнопку {}".format(top_3_workers, top_3_chillers, top_3_chill_reasons, text_if_no_dev), reply_markup=keyboard)
    await state.set_state(State_timer.solo_dev)

@dp.message(State_timer.solo_dev)
async def dev_statistics(message: types.Message, state: FSMContext):
    keyboard, dev = kb.reply_builder_2()
    if message.text in dev and await db.is_admin(message.chat.id):
        dev_statistics_work, dev_statistics_chill, dev_chill_reasons = await db.get_dev_statistics_to_solo_dev(message.text)
        if dev_statistics_work:
            top_3_workers = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_statistics_work])
        else:
            top_3_workers = 'Пока ничего нет'
        if dev_statistics_chill:
            top_3_chillers = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_statistics_chill])
        else:
            top_3_chillers = 'Пока ничего нет'
        if dev_chill_reasons:
            top_3_chill_reasons = '\n'.join([f'{item[0]}: {str(item[1])}' for item in dev_chill_reasons])
        else:
            top_3_chill_reasons = 'Пока ничего нет'
        await message.answer("Смены за последнюю неделю:\n{}\n\nПерерывы за последнюю неделю:\n{}\n\nТоп 3 причины отдыха:\n{}\n".format(top_3_workers, top_3_chillers, top_3_chill_reasons), reply_markup=keyboard)
    elif message.text == 'Назад':
        await message.answer("Статистика для пидоров", reply_markup=kb.keyboard_start_admin)
        await message.answer_sticker(r'CAACAgIAAxkBAAEBgVZlL3tszdN_P9VhMQOw6M6qwuhWswACPxMAAtlwOEpSw_r2yt988jAE')
        await state.clear()


@dp.message(MyFilter('Назад'), State_timer.check_statistics)
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    if not await db.is_admin(message.chat.id):
        await message.answer("Столько дней работал, а ничего не сделал...", reply_markup=kb.keyboard_start)
    else:
        await message.answer("Столько дней работал, а ничего не сделал...", reply_markup=kb.keyboard_start_admin)
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZkplJnJtP-0LHexxexlTBmZyRojmnwAC0QsAAgbzGUjRpvwZO32YlDAE')
    

@dp.message(MyFilter('начать ебашить'))
async def start(message: types.Message, state: FSMContext): 
    await state.update_data(start_time = datetime.datetime.now().time().replace(microsecond=0))
    await message.answer("Погнали нахуй!", reply_markup=kb.keyboard_end)
    await info_dev(message, 'начал ебашить')
    scheduler_2_hours.add_job(print_sheduler_message, trigger='interval', minutes=120, args=[message, "Ты ебашил 2 часа, может пора сделать перерыв?"], id='2_hours_{}'.format(message.chat.id))
    await db.change_is_active(True, message.chat.id)
    await state.set_state(State_timer.start_time)


@dp.message(MyFilter('закончить ебашить'), State_timer.start_time)
async def end(message: types.Message, state: FSMContext):
    await state.set_state(State_timer.end_time)
    await info_dev(message, 'закончил ебашить')
    await state.update_data(end_time = datetime.datetime.now().time().replace(microsecond=0))
    scheduler_2_hours.remove_job(job_id='2_hours_{}'.format(message.chat.id))
    data = await state.get_data()
    time_difference = await delta_time(data)
    hours, seconds = divmod(time_difference.seconds, 3600)
    minutes = seconds // 60
    await message.answer("Ты работал {} часов и {} минут".format(hours, minutes))
    if not await db.is_admin(message.chat.id):
        await message.answer("Надеюсь ты хорошо провел время и сделал хоть что то полезное :)", reply_markup=kb.keyboard_start)
    else: 
        await message.answer("Надеюсь ты хорошо провел время и сделал хоть что то полезное :)", reply_markup=kb.keyboard_start_admin)
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZghlJmTe3n1WMsBEqiQocf_rW2ggtQACfwkAAibJ6UiBeQ1qzGbWLTAE')
    await state.set_state(State_timer.end_time)
    await db.insert_time_info(message.from_user.id, state, time_difference)
    await db.change_is_active(False, message.chat.id)
    await state.clear()


async def info_dev(message: types.Message, text: str):
    admins = await db.all_admins()
    my_login = await db.get_my_login(message.chat.id)
    for data in admins:
        if (int)(data[0]) != message.chat.id:
            await bot.send_message(chat_id=(int)(data[0]), text='{} {}'.format(my_login[0], text))
    
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


@dp.message(MyFilter('/gay'))
async def set_pause(message: types.Message):
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZj5lJnDtesNTQt-Sc4TOXaxEA7a_fAACIAADpP81O6RWbRHXOQEzMAQ')

    
@dp.message(State_timer.pause_reason)
async def pause_reason(message: types.Message, state: FSMContext):
    await state.update_data(pause_reason = message.text)
    await message.answer('Когда закончишь перерыв, нажми кнопку', reply_markup=kb.keyboard_pause)
    await state.update_data(pause_start_time = datetime.datetime.now().time().replace(microsecond=0))
    await state.set_state(State_timer.pause_start_time)
        

@dp.message(MyFilter('вернуться к работе'), State_timer.pause_start_time)
async def with_puree(message: types.Message, state: FSMContext):
    await db.change_is_active(True, message.chat.id)
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
    await message.answer('продолжаем ебашить...', reply_markup=kb.keyboard_end)
    await message.answer_sticker(r'CAACAgIAAxkBAAEBZgZlJmQfGnQaKD1B9A82EEDVfl_yQwACNRQAAkN2IUhAgVSjcyNt0TAE')

@dp.message(MyFilter('активные разрабы'))
async def check_active_dev(message: types.Message):
    if await db.is_admin(message.chat.id):
        is_active = await db.get_is_active()
        result = '\n'.join([f'{item[0]}: {"Ебашит" if item[1] else "Отдыхает"}' for item in is_active])
        await message.answer(result)

async def delta_time(data: dict):
    current_date = datetime.date.today()
    start_datetime = datetime.datetime.combine(current_date, data['start_time'])
    end_datetime = datetime.datetime.combine(current_date, data['end_time'])
    time_difference = end_datetime - start_datetime
    return time_difference
    
async def main() -> None:
    db.create_db()
    db.insert_developers()
    scheduler_2_hours.start()
    scheduler_15_min.start()
    scheduler_before_shift.start()
    scheduler_after_shift.start()
    await dp.start_polling(bot)
 

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
    
    
    
    
