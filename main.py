import base64
import json
import requests
from datetime import datetime, timedelta
from google_api_functions import *
from send_email import send_email
from keys import *

sheet_id = "17bUzAyp989BH3mFF3MsR_ehwHxALi1SW8kAB4y7ZFN4"  # Replace with your Google Sheet ID

# Use this list to exclude any clients that are exceptions to normal contact collection.
clients_to_exclude = ["Resources for Results (Grant Hensel Test Account - Not Billed)"]

date = datetime.now()
month = date.month
year = date.year
today = date.today()
today_str = date.today().strftime("%m/%d/%Y")


#  Get Authorization Token
def get_auth_token():
    url = "https://api.id-visitors.com/Account/GenerateTokenV2Json"
    data = {
        "Email": vv_email,
        "Password": vv_password
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        # Get the token value from json.
        token = response_json.get('token', 'Key not found')
        # print(token)
    else:
        print("Status code:", response.status_code)
        print("Response content:", response.text)

    return token


def get_activity_report(token, month, year):
    url = f"https://api.id-visitors.com/ws/ConsumerReporting/GetConsumerCustomerActivityReport?datelookup={month}-{year}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    query_params = {
        "DateLookup": f"{month}-{year}"
    }

    response = requests.get(url, headers=headers, params=query_params)

    if response.status_code == 200:
        response_json = response.json()
        print(f"Response: {response_json}")
        # Iterate through each JSON, grabbing the client name and Visitors Paid
        data = dict()
        for json in response_json:
            print(json)
            name = json.get('Customer', 'Key not found')
            visitors = json.get('Visitors_Paid', 'Key not found')
            #There may be cases when a name appears twice. If this occurs, take the higher value.
            if name in data:
                data[name] = max(data[name], int(visitors))
            else:
                data[name] = int(visitors)
    else:
        print("Status code:", response.status_code)
        print("Response content:", response.text)
    return data


# Kevin suggested that to get all-time data, I run a series of monthly queries and add them together. #TODO
def get_all_time_activity_report(token, today_str):
    loops = 0
    start_date = datetime.strptime("03/01/2023", "%m/%d/%Y")
    end_date = datetime.strptime(today_str, "%m/%d/%Y")

    # Initialize the data dictionary
    all_data = {}

    while start_date <= end_date:
        loops += 1
        # Format the start and end dates for the current month
        month_start = start_date.strftime("%m/%d/%Y")
        month_end = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        if month_end > end_date:
            month_end = end_date
        month_end_str = month_end.strftime("%m/%d/%Y")

        # API URL and headers
        url = f"https://api.id-visitors.com/ws/ConsumerReporting/GetConsumerCustomerActivityReport?Date_End={month_end_str}&Date_Start={month_start}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        query_params = {
            "Date_End": month_end_str,
            "Date_Start": month_start
        }

        # Make the request
        response = requests.get(url, headers=headers, params=query_params)

        if response.status_code == 200:
            response_json = response.json()
            # print(response_json)
            for json in response_json:
                # print(json)
                name = json.get('Customer', 'Key not found')
                visitors = int(json.get('Visitors_Paid', 0))  # Convert visitors paid to an integer

                # Construct the key
                key = f"{name}"

                # If the key exists, add the visitors to the existing value; otherwise, add the new key-value pair
                if key in all_data:
                    all_data[key] += visitors
                else:
                    all_data[key] = visitors
        else:
            print("Status code:", response.status_code)
            print("Response content:", response.text)

        # Move to the next month
        start_date = month_end + timedelta(days=1)
    return all_data


def get_daily_data(request):

    token = get_auth_token()
    data = get_activity_report(token, month, year)
    write_dict_to_sheet(sheet_id, data, "A2")  # Writes Data For Current Month to "A" Column.

    #If today's month is January, reduce both the month and the year.
    if month == 1:
        data = get_activity_report(token, month - 1, year - 1)
    else:
        data = get_activity_report(token, month - 1, year)
    write_dict_to_sheet(sheet_id, data, "E2") # Writes Data For Last Month to "E" Column

    data = get_all_time_activity_report(get_auth_token(), today_str)
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
