import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_credentials():
    creds = Credentials.from_service_account_file('visitoremail-data-28544584c945.json', scopes=SCOPES)
    return creds

# def get_credentials(): Use Locally
#     creds = None
#     if os.path.exists('token.pickle'):
#         with open('token.pickle', 'rb') as token:
#             creds = pickle.load(token)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open('token.pickle', 'wb') as token:
#             pickle.dump(creds, token)
#     return creds


def find_zeros_in_column(sheet_id, keys_to_exclude=[]):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    # Read values from column A (index 0)
    column_A_range_name = 'A1:A1000' # Change 1000 to the number of rows you want to check
    column_A_result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=column_A_range_name).execute()
    column_A_values = column_A_result.get('values', [])

    # Read values from column B (index 1) where you're looking for zeros
    column_B_range_name = 'B1:B1000'
    column_B_result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=column_B_range_name).execute()
    column_B_values = column_B_result.get('values', [])

    # Combine the values from columns A and B into a dictionary where values from B are "0"
    combined_dict = {column_A_values[index][0]: value[0] for index, value in enumerate(column_B_values) if value and value[0] == "0" and index < len(column_A_values) and column_A_values[index]}

    # Exclude specified keys from the dictionary
    for key in keys_to_exclude:
        combined_dict.pop(key, None)

    return combined_dict


def write_dict_to_sheet(sheet_id, data, range_start):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    # # Clear the sheet
    # clear_request = {"range": "A2:B"}
    # service.spreadsheets().values().clear(spreadsheetId=sheet_id, range="A2:B", body=clear_request).execute()

    # Write the data to the sheet
    values = [[k, v] for k, v in data.items()]
    body = {"values": values}
    result = service.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=range_start, valueInputOption="USER_ENTERED", body=body
    ).execute()
    print(f"{result.get('updatedCells')} cells updated.")

#Extract Historical data from sheet. Only necessary if we need to reduce API queries.
def extract_sheet_data(sheet_id, range):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    # Read the data from the sheet
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=range
    ).execute()
    values = result.get('values', [])

    # Convert the rows to dictionaries
    dictionaries = []
    if values:
        for row in values:
            # Ensure there's enough columns in this row
            if len(row) >= 2:
                # Map the first column to the second as key-value pairs
                dictionaries.append({row[0]: row[1]})
    else:
        print('No data found.')

    return dictionaries


if __name__ == "__main__":
    test = extract_sheet_data("17bUzAyp989BH3mFF3MsR_ehwHxALi1SW8kAB4y7ZFN4", "H:I")
    print(test)

