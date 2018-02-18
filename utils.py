from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from difflib import get_close_matches
from rq import Queue

# helper functions
def next_available_row(worksheet):
    '''returns number of first entry in spreadsheet where the first column is blank'''
    str_list = list(filter(None, worksheet.col_values(1))) # assumes the first column of each entry is filled first, could fail if queuing is weird`
    return len(str_list)+1

def get_closest(m,l):
    '''returns closest match to string m in list l or "UNKNOWN" if no match is close'''
    closest_kwds = get_close_matches(m.lower(), l)
    return closest_kwds[0] if len(closest_kwds) >=1 else "UNKNOWN" 

# load sheet
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
sheetclient = gspread.authorize(creds)
sheet = sheetclient.open("TextingSignups").sheet1

# keywords (first word texted)
keywords = {'join':'Michigan', 'shine':'Florida', 'people':'Pennsylvania', 'change':'Minnesota', 'light':'New York'}

# cache
rowcache = {}
next_row = next_available_row(sheet)

def write_to_sheet(t):
    global next_row
    global rowcache
    print("WRITING GOT CALLED")
    number = t[0]
    msgcount = t[1]
    msg = t[2]
    print("NUMBER,", number, "MSG", msg)
    if msgcount == 1:
        msg = get_closest(msg, keywords.keys())
        if msg in keywords:
            msg = keywords[msg]
    if msgcount == 5 or msgcount == 6:
        msg = get_closest(msg, ['yes','y','no','n'])
        msg = msg[0].lower()
    if number not in rowcache:
        print("NUMBER NOT IN ROWCACHE:", number, rowcache)
        # NOT THREAD-SAFE; FOR SEQUENTIAL ACCESS
        row = next_row
        rowcache[number] = row
        next_row += 1
    else:
        print("NUMBER IN ROWCACHE:", rowcache[number])
        row = rowcache[number]
    print("NUMBER:", number, type(number))
    print("ROWCACHE:", rowcache)
    print("BOOLEAN:", number in rowcache)
    sheet.update_cell(row, 1, number)
    sheet.update_cell(row, msgcount+1, msg)
    return -1
