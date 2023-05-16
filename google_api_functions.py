import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def write_dict_to_sheet(sheet_id, data):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    # Clear the sheet
    clear_request = {"range": "A2:B"}
    service.spreadsheets().values().clear(spreadsheetId=sheet_id, range="A2:B", body=clear_request).execute()

    # Write the data to the sheet
    values = [[k, v] for k, v in data.items()]
    body = {"values": values}
    result = service.spreadsheets().values().update(
        spreadsheetId=sheet_id, range="A2", valueInputOption="RAW", body=body
    ).execute()
    print(f"{result.get('updatedCells')} cells updated.")