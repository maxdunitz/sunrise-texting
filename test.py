import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

sheet = client.open('TextingSignups').sheet1

trucking = sheet.get_all_records()
cell1 = sheet.find("13103571331")
cell2 = sheet.find("3103571331")
print(cell1)
print(cell2)
print(type(cell1))
print(type(cell2))

