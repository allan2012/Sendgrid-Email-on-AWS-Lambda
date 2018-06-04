import json
import sys
import datetime
import pytz
import os
import pymysql
import sendgrid
import python_http_client
from sendgrid.helpers.mail import *

now = datetime.datetime.now()
rds_host  = '<DB_HOST>'
name = '<DB_USERNAME>'
password = '<DB_PASSWORD>'
db_name = '<MY_DB>'
port = 3306


try:
    connection = pymysql.connect(
        rds_host, user=name, 
        passwd=password, 
        db=db_name, 
        connect_timeout=50)
        
except:
    sys.exit()


def log(to_email, message_sent, status):
    """ Log the message to your database"""
    tz = pytz.timezone('Africa/Nairobi')    
    now = datetime.datetime.now(tz)
    str_now = now.strftime('%Y-%m-%d %H:%M:%S') # Format to date('Y-m-d H:i:s)
    with connection.cursor() as cursor:
        sql = "INSERT INTO  outbound " \
              "(email, message_sent, error, cost, status, outgoing_time, alert_type, delivery_status) " \
              "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"          
        cursor.execute(sql, (to_email, message_sent, "No Error", 0, status, str_now, 'email', status))
        connection.commit()


def is_authenticated(authenticate_key):
    """ Authenticate the incomming request """
    auth_key = sendgrid.SendGridAPIClient(apikey=os.environ.get('<AUTHENTICATION_KEY>'))
    if authenticate_key == "<MY_AUTHENTICATION_KEY>":
        return True
    else:
        return False


def lambda_handler(event, context):
    data = {}
    if(is_authenticated(event['key']) == False):
        data = {}
        data['status'] = 'Invalid key!'
        data['code'] = -1
        json_data = json.dumps(data)
        return json_data

    # Get API Keys set in the environmental variables
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('<SENDGRID_API_KEY>'))
    from_email = Email(event['from_email'])
    subject = event['subject']
    to_email = Email(event['to_email'])
    content = Content("text/html", event['body'])
    mail = Mail(from_email, subject, to_email, content)
    mail.template_id = "<MY_SENDGRID_EMAIL_TEMPLATE_ID>"
    body = event['body']

    response = sg.client.mail.send.post(request_body=mail.get())
    status = "Success" if response.status_code == 202 else "Failed"
    log(event['to_email'], event['body'], status)
    data['status_code'] = response.status_code
    #data['status'] = status
    #data['body'] = response.body
    json_data = json.dumps(data)
    return json_data