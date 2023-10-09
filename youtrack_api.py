import database as db
import subprocess
import json

token = 'perm:c2FuZGRvbnk=.NTMtMQ==.WOqZwOZaojM3YlSp4ROaLDCoVnG3iI'

curl_command = [
    'curl',
    '-X', 'GET',
    'https://youtrack.okibiteam.ru/api/issues?fields=project(name),id,summary,resolved',
    '-H', 'Accept: application/json', 
    '-H', 'Authorization: Bearer {}'.format(token), 
    '-H', 'Cache-Control: no-cache', 
    '-H', 'Content-Type: application/json'
]

curl_command2 = [
    'curl',
    '-X', 'GET',
    'https://youtrack.okibiteam.ru/hub/api/rest/users?fields=name,login,id',
    '-H', 'Accept: application/json', 
    '-H', 'Authorization: Bearer {}'.format(token), 
    '-H', 'Cache-Control: no-cache', 
    '-H', 'Content-Type: application/json'
]

curl_command3 = [
    'curl',
    '-X', 'GET',
    'https://youtrack.okibiteam.ru/hub/api/rest/projectteams?fields=id,name&query=has:user',
    '-H', 'Accept: application/json', 
    '-H', 'Authorization: Bearer {}'.format(token), 
    '-H', 'Cache-Control: no-cache', 
    '-H', 'Content-Type: application/json'
]

def get_json_projects():
    try:
        result = subprocess.run(curl_command3, capture_output=True, text=True, check=True)
        json_response = json.loads(result.stdout)
        teams = json_response.get('projectteams', [])
        project_ids = []
        project_names = []
        for team in teams:
            project_ids.append(team.get('id'))
            project_names.append(team.get('name'))
        return project_ids, project_names
        
    except subprocess.CalledProcessError as e:
        print("Error:", e)

def get_jsons_project_teams():
    try:
        result = subprocess.run(curl_command2, capture_output=True, text=True, check=True)
        json_response = json.loads(result.stdout)
        logins = [user["login"] for user in json_response["users"]]
        names = [user["name"] for user in json_response["users"]]
        ids = [user["id"] for user in json_response["users"]]
        return logins, names, ids
    
    except subprocess.CalledProcessError as e:
        print("Error:", e)

def get_jsons_tasks():
    try:
        resolved_values = []
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        json_response = json.loads(result.stdout)
        projects = [item['project'] for item in json_response]
        projects_names = [item['name'] for item in projects]
        tasks = [item['summary'] for item in json_response]
        ids = [item['id'] for item in json_response]
        for item in json_response:
            resolved = item.get('resolved')
            resolved_values.append(resolved)
        return ids, tasks, projects_names, resolved_values
    
    except subprocess.CalledProcessError as e:
        print("Error:", e)
        
    
def get_json_dev_accesses():
    logins, names, ids = get_jsons_project_teams()
    for login in logins:
        curl_command4 = [
            'curl',
            '-X', 'GET',
            'https://youtrack.okibiteam.ru/hub/api/rest/projectteams?fields=id,name&query=user:{}'.format(login),
            '-H', 'Accept: application/json', 
            '-H', 'Authorization: Bearer {}'.format(token), 
            '-H', 'Cache-Control: no-cache', 
            '-H', 'Content-Type: application/json'
        ]
        result = subprocess.run(curl_command4, capture_output=True, text=True, check=True)
        json_response = json.loads(result.stdout)
        names = [team["name"] for team in json_response["projectteams"]]
        db.insert_dev_accsesses(login, names)
    try:
        result = subprocess.run(curl_command3, capture_output=True, text=True, check=True)
        json_response = json.loads(result.stdout) 
        
        
    except subprocess.CalledProcessError as e:
        print("Error:", e) 



        

