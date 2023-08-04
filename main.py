import base64
import json
import requests
from datetime import datetime
from google_api_functions import *
from send_email import send_email
from keys import *

sheet_id = "17bUzAyp989BH3mFF3MsR_ehwHxALi1SW8kAB4y7ZFN4"  # Replace with your Google Sheet ID

# Use this list to exclude any clients that are exceptions to normal contact collection.
clients_to_exclude = ["Resources for Results (Grant Hensel Test Account - Not Billed)"]

date = datetime.now()
month = date.month
today = date.today()


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
            data.update({f"{name}":f"{int(visitors)}"})
    else:
        print("Status code:", response.status_code)
        print("Response content:", response.text)
    return data


# Kevin suggested that to get all-time data, I run a series of monthly queries and add them together. #TODO
def get_all_time_activity_report(token, today):
    url = "https://api.id-visitors.com/ws/ConsumerReporting/GetConsumerCustomerActivityReport?Date_End=" \
          + f"{today}" + "&Date_Start=" + "03/01/2023"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    query_params = {
        "Date_End": f"{today}",
        "Date_Start": f"03/01/2023"
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


def get_daily_data(request):

    token = get_auth_token()
    data = get_activity_report(token, month)
    write_dict_to_sheet(sheet_id, data, "A2")  # Writes Data For Current Month to "A" Column.

    data = get_activity_report(token, month - 1)
    write_dict_to_sheet(sheet_id, data, "E2") # Writes Data For Last Month to "E" Column

    data = get_all_time_activity_report(token, today)
    write_dict_to_sheet(sheet_id, data, "H2")

    return 'Success!', 204


    # if request.method == 'POST':
    #     envelope = json.loads(request.data.decode('utf-8'))
    #     payload = base64.b64decode(envelope['message']['data']).decode('utf-8')
    #     print(f"Payload: {payload}")

    # Put functions here.

    #     return '', 204
    #
    # else:
    #     return 'Method not allowed', 405

if __name__ == "__main__":
    try:
        get_daily_data("")
        no_contacts = list(find_zeros_in_column(sheet_id, clients_to_exclude).keys())
        no_contacts_str = "\n".join(no_contacts)
        if len(no_contacts) >= 1:
            send_email("Clients With 0 Collected Contacts", "Hello,\n The following clients have not collected any "
                                                            "contacts this month and should be investigated: \n\n"
                                                            f"{no_contacts_str}")

    except:
        send_email("Error in VV API Data Gatherer", "See Subject")
