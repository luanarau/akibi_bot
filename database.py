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
        cur.execute("create table if not exists projects("
                    "id serial primary key, "
                    "project text not null, "
                    "project_id text)")
        
        cur.execute("create table if not exists developers("
                    "id serial PRIMARY KEY, "
                    "chat_id text, "
                    "login text, "
                    "name text not null, "
                    "youtracker_id text not null)")
        
        cur.execute("create table if not exists working_tasks("
                    "id serial primary key, "
                    "project_id int, "
                    "task_id text, "
                    "task text, "
                    "resolved text,"
                    "constraint fk_project_id foreign key (project_id) references projects(id))")
        
        cur.execute("create table if not exists working_time("
                    "working_time_id serial PRIMARY KEY, "
                    "developer_id int not null, "
                    "task_id int not null, "
                    "working_date text, "
                    "start_time text, "
                    "end_time text, "
                    "total_working_time text, "
                    "constraint fk_developer_id foreign key (developer_id) references developers(id), "
                    "constraint fk_task_id foreign key (task_id) references working_tasks(id))")
        
        cur.execute("create table if not exists developer_acesses("
                    "id serial not null, "
                    "developer_id int not null, "
                    "project_id int, "
                    "constraint fk_developer_id foreign key (developer_id) references developers(id), "
                    "constraint fk_project_id foreign key (project_id) references projects(id))")
        
        db.commit()
    db.close()

def insert_projects():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    project_ids, project_names = yt.get_json_projects()
    with db.cursor() as cur:
        while project_names and project_ids:
            project_id = (str)(project_ids.pop())
            project_name = (str)(project_names.pop())
            cur.execute("select * from projects where project_id = '{}'".format(project_id))
            checker = cur.fetchone()
            if not checker:
                cur.execute("insert into projects(project, project_id) values('{}', '{}')".format(project_name, project_id))
                print("project {} inserted". format(project_id))
    db.commit()
    db.close() 

def insert_dev_accsesses(login: str, list_of_projects: list) -> None:
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        for project in list_of_projects:
            cur.execute("select * from developer_acesses where developer_id = (select id from developers where login = '{}') and project_id = (select id from projects where project = '{}')".format(login, project))
            fetch_one = cur.fetchone()
            if not fetch_one:
                cur.execute("insert into developer_acesses(developer_id, project_id) values((select id from developers where login = '{}'), (select id from projects where project = '{}'));".format(login, project))
        db.commit()
    db.close()

def get_task_text_by_id(id: int) -> str:  
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    with db.cursor() as cur:
        cur.execute("select task from working_tasks where id = {}".format(id))
        data = cur.fetchone()
        db.close()
    return data

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


def insert_tasks():
    db = psycopg2.connect(host=host, user=user, password=password, database=db_name)
    ids, tasks, projects, resolved = yt.get_jsons_tasks()
    with db.cursor() as cur:
        while ids and tasks:
            project = (str)(projects.pop() + ' Team')
            id = (str)(ids.pop())
            task = (str)(tasks.pop())
            resolved_data = (str)(resolved.pop())
            cur.execute("select * from working_tasks where task_id = '{}';".format(id))
            find_one = cur.fetchone()
            if not find_one:
                cur.execute("insert into working_tasks(project_id, task_id, task, resolved) values((select id from projects where project = %s), %s, %s, %s)", (project, id, task, resolved_data))
                print("task with id: {} inserted". format(id))
    db.commit()
    db.close() 
    
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
        cur.execute("insert into working_time(developer_id, task_id, working_date, start_time, end_time, total_working_time) values((select id from developers where chat_id = '{}' limit 1), {}, '{}', '{}', '{}', '{}')".format(chat_id, data["task_id"], date, data['start_time'], data['end_time'], timedelta))
        db.commit()
    db.close()
    
