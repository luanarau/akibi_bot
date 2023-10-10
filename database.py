from aiogram.fsm.context import FSMContext
import psycopg2
import datetime
import youtrack_api as yt


host = '127.0.0.1'
user = 'postgres'
password = 'bal040102'
db_name = 'postgres'

def create_db():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("create table if not exists developers("
                    "id serial PRIMARY KEY, "
                    "chat_id text, "
                    "login text, "
                    "name text not null, "
                    "youtracker_id text not null)")
        
        
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
                cur.execute("insert into developers(login, name, youtracker_id) values('{}', '{}', '{}');".format(login, name, id))
                if cur:
                    print("developer with id {} added".format(id))
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


        
def get_projects() -> list:
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select project from projects;")
        find_all = cur.fetchall()
        result = [item[0] for item in find_all]
    db.close()
    return result


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
    
