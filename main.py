import requests
from datetime import datetime
from google_api_functions import *
from keys import *

sheet_id = "17bUzAyp989BH3mFF3MsR_ehwHxALi1SW8kAB4y7ZFN4"  # Replace with your Google Sheet ID

today = datetime.now()
month = today.month


#  Get Authorization Token
def get_auth_token():
    url = "https://api.id-visitors.com/Account/GenerateTokenV2Json"
    data = {
        "Email": email,
        "Password": password
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        # Get the token value from json.
        token = response_json.get('token', 'Key not found')
        print(token)
    else:
        print("Status code:", response.status_code)
        print("Response content:", response.text)

    return token


def get_activity_report(token, month):
    url = f"https://api.id-visitors.com/ws/ConsumerReporting/GetConsumerCustomerActivityReport?datelookup={month}-2023"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    query_params = {
        "DateLookup": f"{month}-2023"
    }

    response = requests.get(url, headers=headers, params=query_params)

    if response.status_code == 200:
        response_json = response.json()
        print(response_json)
        # Iterate through each JSON, grabbing the client name and Visitors Paid
        data = dict()
        for json in response_json:
            print(json)
            name = json.get('Customer', 'Key not found')
            visitors = json.get('Visitors_Paid', 'Key not found')
            data.update({f"{name}":f"{visitors}"})
    else:
        print("Status code:", response.status_code)
        print("Response content:", response.text)
    return data


# Runs function to get authentication token.
token = get_auth_token()

data = get_activity_report(token, month)

write_dict_to_sheet(sheet_id, data)
