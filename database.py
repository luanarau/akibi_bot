from aiogram.fsm.context import FSMContext
import requests
from aiogram import types, Bot
from sqlalchemy import create_engine
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import psycopg2
import datetime 
import youtrack_api as yt
import bot as bot
import os

load_dotenv()

host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

## Функция, создающая таблицы в бд

def create_db():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("create table if not exists developers("
                    "id serial PRIMARY KEY, "
                    "chat_id text, "
                    "login text, "
                    "name text not null, "
                    "youtracker_id text not null, "
                    "is_admin boolean not null)")
        
        cur.execute("create table if not exists working_time("
                    "working_time_id serial PRIMARY KEY, "
                    "developer_id int not null, "
                    "working_date date, "
                    "start_time time, "
                    "end_time time, "
                    "total_working_time time, "
                    "constraint fk_developer_id foreign key (developer_id) references developers(id))")
        
        cur.execute("create table if not exists pauses("
                    "pause_id serial PRIMARY KEY, "
                    "pause_reason text, "
                    "developer_id int not null, "
                    "total_pause_time time, "
                    "constraint fk_developer_id foreign key (developer_id) references developers(id))")
        
        cur.execute("create table if not exists dev_schedule("
                    "schedule_id serial PRIMARY KEY, "
                    "developer_id int not null, "
                    "date date, "
                    "start_time time, "
                    "end_time time, "
                    "sheduler_before_id text, "
                    "sheduler_after_id text, "
                    "constraint fk_developer_id foreign key (developer_id) references developers(id))")
        
        cur.execute("create table if not exists is_active("
                    "developer_id serial PRIMARY KEY, "
                    "is_active boolean)")
        db.commit()
    db.close()


## Функция, добавляющая chat_id пользователя при регистрации

async def insert_chat_id(chat_id: str, login: str) -> bool:
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select * from developers where login = '{}';".format(login))
        find_one = cur.fetchone()
        if find_one:
            cur.execute("update developers set chat_id = '{}' where login = '{}'".format(chat_id, login))
            db.commit()
            db.close()
            return False
        else:
            db.close()
            return True

## Функция, добавляющая разработчиков, получаемых через API с youtracker'а

def insert_developers():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    logins, names, ids = yt.get_jsons_project_teams()
    with db.cursor() as cur:
        while logins:
            login = (str)(logins.pop())
            name = (str)(names.pop())
            id = (str)(ids.pop())
            cur.execute("select * from developers where login = '{}'".format(login))
            project_name = cur.fetchone()
            if not project_name:
                cur.execute("insert into developers(login, name, youtracker_id, is_admin) values('{}', '{}', '{}', 'false');".format(login, name, id))
                cur.execute("insert into is_active(is_active) values('false')")
                if cur:
                    print("developer with id {} added".format(id))
        cur.execute("DELETE FROM developers WHERE login = 'admin';")
        cur.execute("DELETE FROM developers WHERE login = 'guest';")
        cur.execute("select * from developers where login = 'luanarau';")
        if not cur.fetchone:  
            cur.execute("insert into developers(login, name, youtracker_id, is_admin) values('luanarau', 'Timofei Balagankii', 'youtracker_id', 'false');")             
    db.commit()
    db.close() 


## Функции возвращающие данные для статистики

async def get_statistics_per_day(id):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    today = datetime.date.today()
    with db.cursor() as cur:
        cur.execute("select working_date, sum(total_working_time) "
                    "from working_time join developers on developer_id = developers.id where developers.chat_id = '{}' and working_date = '{}' group by working_date;".format(id, today))
        data = cur.fetchall()
    db.commit()
    db.close()   
    return data

async def get_statistics_per_week(id):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    today = datetime.date.today()
    one_week_ago = today - datetime.timedelta(days=7)
    with db.cursor() as cur:
        cur.execute("select working_date, sum(total_working_time) "
                    "from working_time join developers on developer_id = developers.id where developers.chat_id = '{}' and working_date > '{}' group by working_date;".format(id, one_week_ago))
        data = cur.fetchall()
    db.commit()
    db.close()   
    return data

async def get_statistics_per_month(id):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    today = datetime.date.today()
    one_week_ago = today - datetime.timedelta(days=30)
    with db.cursor() as cur:
        cur.execute("select working_date, sum(total_working_time) "
                    "from working_time join developers on developer_id = developers.id where developers.chat_id = '{}' and working_date > '{}' group by working_date order by working_date asc;".format(id, one_week_ago))
        data = cur.fetchall()
    db.commit()
    db.close()   
    return data

## Функция добавляющая расписания и job для sheduler 

async def insert_dev_schedule(message, chat_id: str, state: FSMContext, shift_end):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        data = await state.get_data()
        cur.execute("select * from dev_schedule where date = '{}' and developer_id = (select id from developers where chat_id = '{}' limit 1)".format(data['chose_day'], chat_id))
        if not cur.fetchone():
            scheduler_before_id = 'scheduler_before_{}_{}'.format(data['chose_day'], chat_id)
            scheduler_after_id = 'scheduler_after_{}_{}'.format(data['chose_day'], chat_id)
            cur.execute("insert into dev_schedule(developer_id, date, start_time, end_time, sheduler_before_id, sheduler_after_id) values((select id from developers where chat_id = '{}' limit 1), '{}', '{}', '{}', '{}', '{}')".format(chat_id, data['chose_day'], data['chose_time'], shift_end, scheduler_before_id, scheduler_after_id))
            bot.scheduler_before_shift.add_job(bot.print_sheduler_message, 'date', run_date=(str)(data['chose_day']+' '+data['chose_time']+':00'), args=[message, 'Твоя смена началась!'], id=scheduler_before_id)
            bot.scheduler_after_shift.add_job(bot.print_sheduler_message, 'date', run_date=(str)(data['chose_day']+' '+shift_end+':00'), args=[message, 'Твоя смена закончилась!'], id=scheduler_after_id)
            if cur:
                print("INSERTED SCHEDULE")
        else:
            cur.execute("select sheduler_before_id from dev_schedule join developers on dev_schedule.developer_id = developers.id where chat_id = '{}' and date = '{}'".format(chat_id, data['chose_day']))
            before_id = cur.fetchone()
            cur.execute("select sheduler_after_id from dev_schedule join developers on dev_schedule.developer_id = developers.id where chat_id = '{}' and date = '{}'".format(chat_id, data['chose_day']))
            after_id = cur.fetchone()
            scheduler_before_id = 'scheduler_before_{}_{}'.format(data['chose_day'], chat_id)
            scheduler_after_id = 'scheduler_after_{}_{}'.format(data['chose_day'], chat_id)
            bot.scheduler_before_shift.remove_job(before_id[0])
            bot.scheduler_after_shift.remove_job(after_id[0])
            bot.scheduler_before_shift.add_job(bot.print_sheduler_message, 'date', run_date=(str)(data['chose_day']+' '+data['chose_time']+':00'), args=[message, 'Твоя смена началась!'], id=scheduler_before_id)
            bot.scheduler_after_shift.add_job(bot.print_sheduler_message, 'date', run_date=(str)(data['chose_day']+' '+shift_end+':00'), args=[message, 'Твоя смена началась!'], id=scheduler_after_id)
            cur.execute("update dev_schedule set start_time = '{}' where date = '{}' and developer_id = (select id from developers where chat_id = '{}' limit 1)".format(data['chose_time'], data['chose_day'], chat_id))
            cur.execute("update dev_schedule set end_time = '{}' where date = '{}' and developer_id = (select id from developers where chat_id = '{}' limit 1)".format(shift_end, data['chose_day'], chat_id))
            cur.execute("update dev_schedule set sheduler_before_id = '{}' where date = '{}' and developer_id = (select id from developers where chat_id = '{}' limit 1)".format(scheduler_before_id, data['chose_day'], chat_id))
            cur.execute("update dev_schedule set sheduler_after_id = '{}' where date = '{}' and developer_id = (select id from developers where chat_id = '{}' limit 1)".format(scheduler_after_id, data['chose_day'], chat_id))
        db.commit()
    db.close()

## Функция для провери наличия chat_id в базе для регистрации

async def authorize(chat_id: str) -> bool:
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select * from developers where chat_id = '{}';".format(chat_id))
        user_id = cur.fetchone()
        db.close()
        if not user_id:
            return True
        else:
            return False

## Функция для добавления значений в базу working_time

async def insert_time_info(chat_id: str, state: FSMContext, timedelta) -> None:
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        data = await state.get_data()
        date = (str)(datetime.datetime.now().date())
        cur.execute("insert into working_time(developer_id, working_date, start_time, end_time, total_working_time) values((select id from developers where chat_id = '{}' limit 1), '{}', '{}', '{}', '{}')".format(chat_id, date, data['start_time'], data['end_time'], timedelta))
        db.commit()
    db.close()

## Функция для добавления значений в базу pauses

async def insert_pause_time_info(chat_id: str, state: FSMContext, time_difference) -> None:
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        data = await state.get_data()
        cur.execute("insert into pauses(pause_reason, developer_id, total_pause_time) values('{}', (select id from developers where chat_id = '{}' limit 1), '{}')".format(data['pause_reason'], chat_id, time_difference))
        db.commit()
    db.close()

## Функция для проверки есть ли уже расписание на какой либо день задаваемый пользователем

async def check_for_schedule(chat_id: str, date) -> bool:
    state = False
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select * from dev_schedule where developer_id = (select id from developers where chat_id = '{}' limit 1) and date = '{}'".format(chat_id, date))
        if cur.fetchone:
            state = True
    db.close()
    return state

## Функция возвращающая все расписание пользователя

async def get_full_schedule(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("SELECT date, start_time, end_time FROM dev_schedule WHERE date <= NOW() + INTERVAL '1 week' and date >= NOW() and developer_id = (select id from developers where chat_id = '{}' limit 1) order by date asc".format(chat_id))
        data = cur.fetchall()
    db.close()
    return data

## Функция меняющая статус работы

async def change_is_active(flag: bool, chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        if flag:
            cur.execute("update is_active set is_active = 'true' where developer_id = (select id from developers where chat_id = '{}' limit 1)".format(chat_id))
        else:
            cur.execute("update is_active set is_active = 'false' where developer_id = (select id from developers where chat_id = '{}' limit 1)".format(chat_id))
        db.commit()
    db.close()

## Функция возвращающая статус работы

async def get_is_active():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select developers.login, is_active.is_active from is_active join developers on developer_id = developers.id")
        is_active = cur.fetchall()
        db.commit()
    db.close()
    return is_active

## Функция возвращающая статус админа

async def is_admin(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select is_admin from developers where chat_id = '{}'".format(chat_id))
        is_admin = cur.fetchone()[0]
        db.commit()
    db.close()
    return is_admin

## Функция возвращающая всех админов

async def all_admins():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select chat_id from developers where is_admin = 'true'")
        all_admins = cur.fetchall()
        db.commit()
    db.close()
    return all_admins


## Функция возвращающая логин пользователя

async def get_my_login(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select login from developers where chat_id = '{}'".format(chat_id))
        login = cur.fetchone()
        db.commit()
    db.close()
    return login
 
 
## Функция меняющая статус админа
    
async def grant_admin(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("update developers set is_admin = 'true' where chat_id = '{}'".format(chat_id))
        db.commit()
    db.close()
    
## Функция возвращающая всех разработчиков   

def get_dev():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select login from developers where chat_id is not null;")
        dev = cur.fetchall()
    db.close()
    return dev

## Функции возвращающие данные для статистики

async def get_dev_statistics_to_admin():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select login, sum(total_working_time) as twt from working_time "
                    "join developers on working_time.developer_id = developers.id group by login order by twt desc limit 3")
        dev_statistics_work = cur.fetchall()

        cur.execute("select login, sum(total_pause_time) as tpt from pauses "
                    "join developers on pauses.developer_id = developers.id group by login order by tpt desc limit 3")
        dev_statistics_chill = cur.fetchall()
        
        cur.execute("select pause_reason, count(pause_reason) as cpr from pauses "
                    "group by pause_reason order by cpr desc limit 3")
        dev_statistics_chill_reasons = cur.fetchall()
        
        db.commit()
    db.close()
    return dev_statistics_work, dev_statistics_chill, dev_statistics_chill_reasons

async def get_dev_statistics_to_solo_dev(login: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
          
        cur.execute("select working_date, sum(total_working_time) as twt from working_time "
                    "join developers on working_time.developer_id = developers.id where login = '{}' group by working_date order by working_date desc limit 7".format(login))
        week_statistics_work = cur.fetchall()
        
        cur.execute("select developers.login as tag, sum(total_pause_time) as tpt from pauses "
                    "join developers on pauses.developer_id = developers.id where login = '{}' group by tag order by tag desc limit 7".format(login))
        week_statistics_chill = cur.fetchall()
        
        cur.execute("select pause_reason, count(pause_reason) as cpr from pauses join developers on pauses.developer_id = developers.id "
                    "where developers.login = '{}' group by pause_reason order by cpr desc limit 3".format(login))
        chill_reasons = cur.fetchall()
        db.commit()
    db.close()
    return week_statistics_work, week_statistics_chill, chill_reasons


## Функция удаляющая аккаунт пользователя из базы

async def remove_acc(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("update developers set is_admin = false where chat_id = '{}'".format(chat_id))
        cur.execute("update developers set chat_id = null where chat_id = '{}'".format(chat_id))
        db.commit()
    db.close()

## Нужна для заполнения нерабочих дней нулями

async def insert_zero(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select * from working_time join developers on working_time.developer_id = developers.id where working_date = CAST(CURRENT_TIMESTAMP AS DATE) and developers.chat_id = '{}'".format(chat_id))
        check = cur.fetchone()
        if not check:
            cur.execute("insert into working_time(developer_id, working_date, total_working_time) values((select id from developers where chat_id = '{}' limit 1), CAST(CURRENT_TIMESTAMP AS DATE), '00:00:00')".format(chat_id))
            if cur:
                print("inserted zero worktime")
        db.commit()
    db.close()


## Функции для отрисовки графиков

async def productivity_solo(message: types.Message, login: str):
    engine = create_engine(os.getenv('POSTGRES_ENGINE'))
    df = pd.read_sql("select working_date, sum(total_working_time) from working_time where developer_id = (select id from developers "
                     "where login = '{}') group by working_date order by working_date asc limit 7;".format(login), engine)
    if not df.empty:
        df['sum'] = df['sum'].dt.total_seconds() / 3600
        x_values = list(df['working_date'].astype(str))
        y_values = list(df['sum'])
        plt.figure()
        plt.bar(x_values, y_values, color ='maroon', width = 0.4)
        plt.xlabel("Дни за последнюю неделю")
        plt.ylabel("Часы работы")
        plt.title("Продуктивность {}".format(login))
        plt.savefig('graphics/{}.png'.format(login))
        requests.post(f'https://api.telegram.org/bot{bot.bot_token}/sendPhoto', data={'chat_id': message.chat.id}, files={'photo': open('graphics/{}.png'.format(login), 'rb')})
        
async def productivity_solo_month(message: types.Message):
    engine = create_engine(os.getenv('POSTGRES_ENGINE'))
    df = pd.read_sql("select working_date, sum(total_working_time) from working_time where developer_id = (select id from developers "
                     "where chat_id = '{}') group by working_date order by working_date asc limit 30;".format(message.chat.id), engine)
    engine.dispose()
    if not df.empty:
        df['sum'] = df['sum'].dt.total_seconds() / 3600
        x_values = list(df['working_date'].astype(str))
        y_values = list(df['sum'])
        plt.figure()
        plt.ylim(0, 24)
        plt.bar(x_values, y_values, color ='maroon', width = 0.4)
        plt.xlabel("Дни за последний месяц")
        plt.ylabel("Часы работы")
        plt.savefig('graphics/{}.png'.format(message.chat.id))
        requests.post(f'https://api.telegram.org/bot{bot.bot_token}/sendPhoto', data={'chat_id': message.chat.id}, files={'photo': open('graphics/{}.png'.format(message.chat.id), 'rb')})
        
async def productivity_solo_week(message: types.Message):
    engine = create_engine(os.getenv('POSTGRES_ENGINE'))
    df = pd.read_sql("select working_date, sum(total_working_time) from working_time where developer_id = (select id from developers "
                     "where chat_id = '{}') group by working_date order by working_date asc limit 7;".format(message.chat.id), engine)
    engine.dispose()
    if not df.empty:
        df['sum'] = df['sum'].dt.total_seconds() / 3600
        x_values = list(df['working_date'].astype(str))
        y_values = list(df['sum'])
        plt.figure()
        plt.ylim(0, 24)
        plt.bar(x_values, y_values, color ='maroon', width = 0.4)
        plt.xlabel("Дни за ближайшую неделю")
        plt.ylabel("Часы работы")
        plt.savefig('graphics/{}.png'.format(message.chat.id))
        requests.post(f'https://api.telegram.org/bot{bot.bot_token}/sendPhoto', data={'chat_id': message.chat.id}, files={'photo': open('graphics/{}.png'.format(message.chat.id), 'rb')})
        
async def productivity_all_dev(message: types.Message):
    engine = create_engine(os.getenv('POSTGRES_ENGINE'))
    df_query = "select login, working_date, sum(total_working_time) from working_time join developers on working_time.developer_id = developers.id group by working_date, login order by working_date asc limit 7;"
    df = pd.read_sql(df_query, engine)
    
    df2_query = "select login, sum(total_working_time) from working_time join developers on working_time.developer_id = developers.id group by login;"
    df2 = pd.read_sql(df2_query, engine)
    
    engine.dispose()
    if not df.empty:
        plt.figure()
        df['sum'] = df['sum'].dt.total_seconds() / 3600
        x_values = list(df['working_date'].astype(str))
        unique = df.login.unique()
        
        for login in unique:
            filtered_df = df[df['login'] == login]
            x_values = list(filtered_df['working_date'].astype(str))
            y_values = list(filtered_df['sum'])
            plt.plot(x_values, y_values, label='{}'.format(login))
        plt.ylim(0, 16)
        plt.legend()
        plt.xlabel("Дни за ближайшую неделю")
        plt.ylabel("Часы работы")
        plt.title("Продуктивность команды за последнюю неделю")
        plt.savefig('graphics/productivity.png'.format(login))
        requests.post(f'https://api.telegram.org/bot{bot.bot_token}/sendPhoto', data={'chat_id': message.chat.id}, files={'photo': open('graphics/productivity.png', 'rb')})
        
    if not df2.empty:
        plt.figure()
        df2['sum'] = df2['sum'].dt.total_seconds() / 3600
        plt.bar(df2['login'], df2['sum'], color ='maroon', width = 0.4)
        plt.ylim(0, 16)
        plt.legend()
        plt.ylabel("Сумарные часы работы")
        plt.title("Продуктивность команды за последнюю неделю")
        plt.savefig('graphics/productivity2.png'.format(login))
        requests.post(f'https://api.telegram.org/bot{bot.bot_token}/sendPhoto', data={'chat_id': message.chat.id}, files={'photo': open('graphics/productivity2.png', 'rb')})
        
        