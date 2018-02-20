from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from difflib import get_close_matches
from rq import Queue

# load sheet
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
sheetclient = gspread.authorize(creds)
sheet = sheetclient.open("TextingSignups").sheet1

# helper functions
def get_closest(m,l):
    '''returns closest match to string m in list l or "UNKNOWN" if no match is close'''
    closest_kwds = get_close_matches(m.lower(), l)
    return closest_kwds[0] if len(closest_kwds) >=1 else "UNKNOWN" 

# keywords (first word texted)
keywords = {'join':'Michigan', 'shine':'Florida', 'people':'Pennsylvania', 'change':'Minnesota', 'light':'New York'}

def write_to_sheet(t):
    print("START:", datetime.now())
    global next_row
    number = t[0]
    msgcount = t[1]
    msg = t[2]
    row = t[3]
    if msgcount == 1:
        msg = get_closest(msg, keywords.keys())
        if msg in keywords:
            msg = keywords[msg]
    if msgcount == 5 or msgcount == 6:
        msg = get_closest(msg, ['yes','y','no','n'])
        msg = msg[0].lower()
    sheet.update_cell(row, 1, number)
    if msgcount == 4:
        sheet.update_cell(row, msgcount+1, msg.split(" ")[0]) # first name
        sheet.update_cell(row, msgcount+2, msg.split(" ")[-1]) # last name
    elif msgcount > 4:
        sheet.update_cell(row, 1, number)
        sheet.update_cell(row, msgcount+2, msg)
    else:
        sheet.update_cell(row, msgcount+1, msg)
    print("END: ", datetime.now())
    return -1
