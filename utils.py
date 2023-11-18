import openai
import json
import os
import re

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


openai.api_key = os.environ["OPENAI_API_KEY"]


def escape_markdown(string: str) -> str:
    """
    Function to escape markdown syntax
    """

    return (
        string.replace("_", "\_")
        .replace("*", "\*")
        .replace("[", "\[")
        .replace("]", "\]")
        .replace("(", "\(")
        .replace(")", "\)")
        .replace("~", "\~")
        .replace(">", "\>")
        .replace("#", "\#")
        .replace("+", "\+")
        .replace("-", "\-")
        .replace("=", "\=")
        .replace("|", "\|")
        .replace("{", "\{")
        .replace("}", "\}")
        .replace(".", "\.")
        .replace("!", "\!")
        .replace(",", "\,")
    )


def force_private(message: callable) -> bool:
    """
    Function to force chat into private chat
    """
    if message.chat.type == "private":
        return True

    return False


def generate_chatgpt_answer(user_id: int, prompt: str) -> str:
    """
    Chat GPT function
    """

    try:
        # Make sure user have account, even if it not started bot.
        folder_path = f"Accounts/{user_id}"
        file_path = f"Accounts/{user_id}/history.json"

        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        if not os.path.exists(file_path):
            with open(file_path, "w") as file:
                json.dump([], file)

        # Read history and add user role to history
        with open(file_path, "r") as file:
            history = json.load(file)

        if len(history) == 0:
            history.append(
                {"role": "system", "content": os.environ["SYSTEM_PROMPT"]}
            )

        history.append({"role": "user", "content": prompt})

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=history,
        )
        print(
            f'{completion["usage"]["prompt_tokens"]} prompt tokens counted by'
            " the OpenAI API."
        )

        gpt_result = completion.choices[0].message.content
        # Add GPT prompt to history
        history.append({"role": "assistant", "content": gpt_result})

        # Save new history
        with open(file_path, "w") as file:
            json.dump(history, file, indent=2, ensure_ascii=False)

        # Return chat answer
        return gpt_result

    # Handle errors
    except Exception as ex:
        return f"Error due to {ex}"
    

def send_email(to_address: str, subject: str, body: str):
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
    

def send_contact_number_to_email(phone: str):
    receiver = os.environ["RECEIVER_EMAIL_ADDRESS"]  # EXAMPLE USAGE
    subject = "Contact number of candidate"
    body = f"The contact number of candidate is: {phone}" # CAN BE REFORMED USING HTML CONTENT

    send_email(receiver, subject, body)
    

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

