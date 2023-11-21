import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re



def send_email(to_address, subject, body):

    # NEED TO SETUP EMAIL CREDENTIALS
    smtp_server = "smtp.gmail.com" # ASSUME WE ARE USING GMAIL ENGINE
    smtp_port = 587
    smtp_username = os.environ["SENDER_EMAIL_ADDRESS"]   # EXAMPLE USAGE
    smtp_password = os.environ["EMAISENDER_EMAIL_PASS"]  # EXAMPLE USAGE


    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # CONNECT TO SMTP AND SEND EMAIL
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_address, msg.as_string())


def send_toker_error(status_code, response):

    receiver = os.environ["RECEIVER_EMAIL_ADDRESS"] 
    subject = "Contact number of candidate"
    body = f"Failed to get access token. Status code: {status_code}, Response: {response}" # CAN BE REFORMED USING HTML CONTENT

    send_email(receiver, subject, body)


def send_contact_number_to_email(phone):

    receiver = os.environ["RECEIVER_EMAIL_ADDRESS"]  
    subject = "Contact number of candidate"
    body = f"The contact number of candidate is: {phone}" # CAN BE REFORMED USING HTML CONTENT

    send_email(receiver, subject, body)



def get_access_token():

    client_id = os.environ['AVITO_CLIENT_ID']
    client_secret = os.environ['AVITO_CLIENT_SECRET']
    grant_type = 'client_credentials'  # FIXED PARAM

    # AUTH OF AVITO
    token_endpoint = "https://api.avito.ru/token"

    # HEADER
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # NEEDED PARAM FROM AVITO ACCOUNT
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': grant_type
    }

    # API CALL FOR TOKEN
    response = requests.post(token_endpoint, headers=headers, data=data)

    if response.status_code == 200:
        # Save the token to token.json in the desired format
        access_token = response.json().get('access_token')
        with open('temp/token.json', 'w') as file:
            json.dump({'access': {'token': access_token}}, file)
    else:
        send_toker_error(response.status_code, response.text)
        print("Response content:", response.content)



def check_contact_number(text: str):
    
    # Validaiton for  phone number format
    patterns = [
        r'\+(\d{1,2})\((\d{3})\)(\d{3}-\d{2}-\d{2})',   # +7(123)456-78-90
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # IF MATHED PHONE IS FOUND, EMAIL SEND FUNCTION CAN BE CALLED
            send_contact_number_to_email(match.group(0))
            return True

    return False


def read_access_token():
    with open('temp/token.json', 'r') as file:
        data = json.load(file)
        return data.get('access', {}).get('token', '')