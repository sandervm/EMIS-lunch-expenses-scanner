import requests
import os

EMIS_API_KEY = 'e2f556c3d3a7759dc4458f55ddd80684'
API_LOGIN_URL = 'https://emis.elements.nl/api/v1/auth/login'
API_EXPENSES_URL = 'https://emis.elements.nl/api/v1/expenses'

def authenticate(username, password):
    headers = {
        'X-Emis-Api-Key': EMIS_API_KEY,
        'User-Agent': 'EMIS-expenses-scanner/0.0.1',
    }
    payload = { 'username': username, 'password': password }
    response = requests.request(
        'POST', API_LOGIN_URL, data=payload, headers=headers)

    assert response.status_code == 200, 'Login failed'

    return response.json()['data']['sessionToken']

def submit_expenses(session_token, properties):
    payload = {
        'type': 6,
        'amount': properties['price'],
        'date': properties['date'],
        'description': 'Lunch'
    }

    headers = {
        'X-Emis-Api-Key': EMIS_API_KEY,
        'X-Emis-Api-Session-Token': session_token,
    }

    with open(properties['image'], 'rb') as file:
        files = {
            'file': (os.path.basename(properties['image']), file),
        }

        return requests.request(
            'POST', API_EXPENSES_URL, data=payload, files=files, headers=headers)
