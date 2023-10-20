from aiogram.fsm.context import FSMContext
import psycopg2
import datetime
import youtrack_api as yt
import bot as bot


host = 'localhost'
port = '5432'
user = 'postgres'
password = 'bal040102'
db_name = 'postgres'

def create_db():
    db = psycopg2.connect(host=host, port=port, user=user, password=password, database=db_name)
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

    db.commit()
    db.close() 
    
    
async def get_tasks(id):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select working_tasks.id, working_tasks.task from working_tasks "
                    "join developer_acesses on working_tasks.project_id = developer_acesses.project_id "
                    "join developers on developer_acesses.developer_id = developers.id "
                    "where chat_id = '{}' and working_tasks.resolved = 'None';".format(id))
        data = cur.fetchall()
    db.commit()
    db.close()   
    return data

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

async def insert_time_info(chat_id: str, state: FSMContext, timedelta) -> None:
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        data = await state.get_data()
        date = (str)(datetime.datetime.now().date())
        cur.execute("insert into working_time(developer_id, working_date, start_time, end_time, total_working_time) values((select id from developers where chat_id = '{}' limit 1), '{}', '{}', '{}', '{}')".format(chat_id, date, data['start_time'], data['end_time'], timedelta))
        db.commit()
    db.close()

async def insert_pause_time_info(chat_id: str, state: FSMContext, time_difference) -> None:
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        data = await state.get_data()
        cur.execute("insert into pauses(pause_reason, developer_id, total_pause_time) values('{}', (select id from developers where chat_id = '{}' limit 1), '{}')".format(data['pause_reason'], chat_id, time_difference))
        db.commit()
    db.close()

async def check_for_schedule(chat_id: str, date) -> bool:
    state = False
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select * from dev_schedule where developer_id = (select id from developers where chat_id = '{}' limit 1) and date = '{}'".format(chat_id, date))
        if cur.fetchone:
            state = True
    db.close()
    return state

async def get_full_schedule(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("SELECT date, start_time, end_time FROM dev_schedule WHERE date <= NOW() + INTERVAL '1 week' and date >= NOW() and developer_id = (select id from developers where chat_id = '{}' limit 1) order by date asc".format(chat_id))
        data = cur.fetchall()
    db.close()
    return data

async def change_is_active(flag: bool, chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        if flag:
            cur.execute("update is_active set is_active = 'true' where developer_id = (select id from developers where chat_id = '{}' limit 1)".format(chat_id))
        else:
            cur.execute("update is_active set is_active = 'false' where developer_id = (select id from developers where chat_id = '{}' limit 1)".format(chat_id))
        db.commit()
    db.close()
    
async def get_is_active():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select developers.login, is_active.is_active from is_active join developers on developer_id = developers.id")
        is_active = cur.fetchall()
        db.commit()
    db.close()
    return is_active
    
async def is_admin(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select is_admin from developers where chat_id = '{}'".format(chat_id))
        is_admin = cur.fetchone()[0]
        db.commit()
    db.close()
    return is_admin

async def all_admins():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select chat_id from developers where is_admin = 'true'")
        all_admins = cur.fetchall()
        db.commit()
    db.close()
    return all_admins

async def get_my_login(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select login from developers where chat_id = '{}'".format(chat_id))
        login = cur.fetchone()
        db.commit()
    db.close()
    return login
    
async def grant_admin(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("update developers set is_admin = 'true' where chat_id = '{}'".format(chat_id))
        db.commit()
    db.close()
    
def get_dev():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select login from developers where chat_id is not null;")
        dev = cur.fetchall()
    db.close()
    return dev
    
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
    
async def remove_acc(chat_id: str):
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("update developers set is_admin = false where chat_id = '{}'".format(chat_id))
        cur.execute("update developers set chat_id = null where chat_id = '{}'".format(chat_id))
        db.commit()
    db.close()