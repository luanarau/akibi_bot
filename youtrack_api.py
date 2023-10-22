import database as db
from dotenv import load_dotenv
import os
import subprocess
import json

load_dotenv()

api_token = os.getenv('API_TOKEN')

curl_command = [
    'curl',
    '-X', 'GET',
    'https://youtrack.okibiteam.ru/hub/api/rest/users?fields=name,login,id',
    '-H', 'Accept: application/json', 
    '-H', 'Authorization: Bearer {}'.format(api_token), 
    '-H', 'Cache-Control: no-cache', 
    '-H', 'Content-Type: application/json'
]

def get_jsons_project_teams():
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        json_response = json.loads(result.stdout)
        logins = [user["login"] for user in json_response["users"]]
        names = [user["name"] for user in json_response["users"]]
        ids = [user["id"] for user in json_response["users"]]
        return logins, names, ids
    
    except subprocess.CalledProcessError as e:
        print("Error:", e)


