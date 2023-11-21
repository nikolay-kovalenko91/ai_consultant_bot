import requests
import time
import os
from utils import get_access_token, check_contact_number, read_access_token
from message_handler import generate_chatgpt_answer
import message_handler




user_id = os.environ["AVITO_USER_ID"]


def send_message_back(reply_message, chat_id):
    send_message_api_endpoint = f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages"

    access_token = read_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'message': {
            'text': reply_message
        },
        'type': 'text'
    }
    response = requests.post(send_message_api_endpoint, headers=headers, json=payload)

    if response.status_code == 200:
        return None
    elif response.status_code == 403:

        # Handle 403 error by calling another function and trying the API call again
        print("NEED TO GET NEW TOKEN")
        get_access_token()
        send_message_back(reply_message, chat_id)
    else:
        # MESSAGE CAN BE SEND TO EMAIL
        print(f"API call failed with status code {response.status_code}")
        return None


def end_conversation(reply_message, chat_id):
    send_message_api_endpoint =  f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages"

    access_token = read_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'message': {
            'text': reply_message
        },
        'type': 'text'
    }
    response = requests.post(send_message_api_endpoint, headers=headers, json=payload)

    if response.status_code == 200:
        return None
    elif response.status_code == 403:

        # Handle 403 error by calling another function and trying the API call again
        print("NEED TO GET NEW TOKEN")
        get_access_token()
        send_message_back(reply_message, chat_id)
    else:
        # MESSAGE CAN BE SEND TO EMAIL
        print(f"API call failed with status code {response.status_code}")
        return None


def get_new_messages():

    query='unread_only=true'

    chats_api_endpoint = f'https://api.avito.ru/messenger/v2/accounts/{user_id}/chats{query}'

    access_token = read_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(chats_api_endpoint, headers=headers)

    if response.status_code == 200:

        full_messages = response.json()
        print(full_messages)
        for each_message in full_messages['chats']:

            # SEND MESSAGE TO GPT FUNCTION NEEDS TO BE CALLED FOR EACH NEW MESSAGE
            chat_id = each_message['id']
            message_content = each_message['last_message']['content']['link']['text']

            # user_id  -->  chat_id
            # prompt   -->  message_content

            phone_status = check_contact_number(message_content, chat_id)
            if phone_status:
                end_message = "Thanks for your time! We will get you touch very soon!"
                end_conversation(end_message)
            else:
                result = generate_chatgpt_answer(chat_id, message_content)
                send_message_back(message_handler.escape_markdown(result), chat_id)

    # IF TOKEN IS EXPIRED GET NEW TOKEN       
    elif response.status_code == 403:

        # Handle 403 error by calling another function and trying the API call again
        print("NEED TO GET NEW TOKEN")
        get_access_token()
        get_new_messages()

    else:
        # MESSAGE CAN BE SEND TO EMAIL
        print(f"API call failed with status code {response.status_code}")

if __name__ == '__main__':
    while True:
        get_new_messages()
        print("API HAS BEEEN CALLED")
        time.sleep(10)  # Sleep for 10 seconds
