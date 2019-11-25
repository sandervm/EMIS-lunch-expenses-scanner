import requests
import os

API_LOGIN_URL = 'https://emis.elements.nl/api/v1/auth/login'
API_EXPENSES_URL = 'https://emis.elements.nl/api/v1/expenses'

def authenticate(api_key, username, password):
    headers = {
        'X-Emis-Api-Key': api_key,
        'User-Agent': 'EMIS-lunch-expenses-scanner/0.0.1',
    }
    payload = { 'username': username, 'password': password }
    response = requests.request(
        'POST', API_LOGIN_URL, data=payload, headers=headers)

    assert response.status_code == 200, 'Login failed'

    return response.json()['data']['sessionToken']

def submit_expenses(api_key, session_token, properties):
    payload = {
        'type': 6,
        'amount': properties['price'],
        'date': properties['date'],
        'description': 'Lunch'
    }

    headers = {
        'X-Emis-Api-Key': api_key,
        'X-Emis-Api-Session-Token': session_token,
        'User-Agent': 'EMIS-lunch-expenses-scanner/0.0.1',
    }

    with open(properties['image'], 'rb') as file:
        files = {
            'file': (os.path.basename(properties['image']), file),
        }

        return requests.post(
            API_EXPENSES_URL, data=payload, files=files, headers=headers)
