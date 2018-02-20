from flask import Flask, request, session
from twilio import twiml
from twilio.twiml.messaging_response import MessagingResponse
import redis
from rq import Queue
from worker import conn
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread

## HELPER FUNCTION ## 
def next_available_row(worksheet):
    '''returns number of first entry in spreadsheet where the first column is blank'''
    str_list = list(filter(None, worksheet.col_values(1)))
    number_dict = dict([(v,i) for i,v in enumerate(str_list)]) 
    return (len(str_list)+1, number_dict)

## LOAD THE SPREADSHEET ## 
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
sheetclient = gspread.authorize(creds)
sheet = sheetclient.open("TextingSignups").sheet1

SECRET_KEY = 'put_your_secret_key_here'
app = Flask(__name__)
app.secret_key = SECRET_KEY

q = Queue(connection=conn)

next_row, rowcache = next_available_row(sheet)
print("THIS IS HAPPENING")

@app.route("/", methods=['GET', 'POST'])
def sms():
    ## SET EXPIRATION TIME FOR COOKIES ##
    now = datetime.utcnow() # current time, for debugging
    print("START: ", now)
    expires=now + timedelta(hours=4)

    ## GET INCOMING INFO ##
    msg = request.form['Body'] # THE TEXT ITSELF
    number = request.form['From'] # THE SENDER'S NUMBER
    number = number[1:] #strip off the '+' which google sheets deletes
    msgcount = int(session.get('msgcount', 0)) # THE NUMBER OF TIMES THE PERSON HAS TEXTED IN, INFERRED FROM UNEXPIRED COOKIES, IF ANY

    ## CRAFT REPLY (TAKING NOTE TO CREATE A NAME COOKIE WHEN THE NAME COMES IN) ##
    reply = None
    if msgcount == 0:
        reply = "Welcome to Sunrise! To stay in the loop, text us your email address"
    elif msgcount == 1:
        reply = "Super! Now send us your zipcode so we can connect you with different opportunities Sunrise has to offer!"
    elif msgcount == 2:
        reply = "Awesome! What is your full name?"
    elif msgcount == 3:
        reply = "Great. Are you interested in getting candidates in your community to sign the No Fossil Fuel Money Pledge? (Y/N)"
    elif msgcount == 4:
        name = session.get('firstname', 'climate champion')
        reply = "Fantastic, {}! Are you interested in learning more about Sunrise Semester? (Y/N)".format(name)
    elif msgcount == 5:
        name = session.get('firstname', 'climate champion')
        reply = "Thanks, {}! Looking forward to taking action with you this year. Together, we'll make climate change an urgent priority, get fossil fuel money out of our politics, and elect leaders who will stand up for the health and well-being of all people. Let's shine bright!".format(name)
   
    ## SET UP RESPONSE ##
    resp = MessagingResponse()
    resp.message(reply)
 
    ## SET NEW MESSAGE COUNT COOKIE ##
    msgcount += 1
    session['msgcount'] = msgcount 

    ## SET FIRSTNAME COOKIE ##
    if msgcount == 4:
        firstname = msg.split(" ")[0]
        session['firstname'] = firstname

    ## GET ROW ##
    global next_row
    global rowcache
    if number not in rowcache:
        row = next_row
        rowcache[number] = row
        next_row += 1
    else:
        row = rowcache[number]
    print("LOGGED: ", number, msgcount, msg, row)
    
    ## ENQUEUE MESSAGE ##
    from utils import write_to_sheet
    res = q.enqueue(write_to_sheet, (number, msgcount, msg, row))
    print("END TIME: ", datetime.utcnow()) 
    return str(resp)
