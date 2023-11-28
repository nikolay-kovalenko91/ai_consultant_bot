import requests
import time
import os
import argparse
import logging
from message_handler import generate_chatgpt_answer
from constants import (
    CLIENT_ID,
    CLIENT_SECRET,
    GRAND_TYPE,
    AVITO_USER_ID,
    BASE_FOLDER,
    SUB_FOLDER,
    POLLING_INTERVAL,
)

# Configure logging
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


def parse_args():
    """
    Function to parse command-line arguments
    """
    parser = argparse.ArgumentParser(description="Get messaged only")
    parser.add_argument("--dry", action="store_true", help="Run in dry mode")
    return parser.parse_args()


def get_access_token() -> None:
    """
    Function to get new access token
    """
    global ACCESS_TOKEN

    # Set up headers
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Params
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": GRAND_TYPE,
    }

    # Make the API call
    response = requests.post(
        "https://api.avito.ru/token", headers=headers, data=data
    )

    if response.status_code == 200:
        # Save the token to token.json in the desired format
        ACCESS_TOKEN = response.json().get("access_token")
    else:
        logging.error(f"Token error : {response.status_code}, {response.text}")


def send_message_back(reply_message: str, chat_id: str) -> None:
    """
    Function to send message back to user
    """

    # If access token is none get new one
    if ACCESS_TOKEN is None:
        get_access_token()

    # Set up headers
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Prepare the payload
    payload = {"message": {"text": reply_message}, "type": "text"}

    # Make the API call
    response = requests.post(
        (
            f"https://api.avito.ru/messenger/v1/accounts/{AVITO_USER_ID}/"
            f"chats/{chat_id}/messages"
        ),
        headers=headers,
        json=payload,
    )

    # Check the response status
    if response.status_code == 200:
        logging.info(
            f"Message from chat_id = {chat_id} successfully answered "
        )
    elif response.status_code == 403:
        # Handle 403 error by calling  function and call api back
        logging.debug("Need to get token")
        get_access_token()
        send_message_back(reply_message, chat_id)
    else:
        logging.error(
            (
                "Send message back is failed. "
                f"Error: {response.text}. Payload: {payload}"
            )
        )


def get_new_messages():
    """
    Function to get new messages from Avito
    """

    # If access token is None, obtain a new one
    if ACCESS_TOKEN is None:
        get_access_token()

    path = os.path.join(BASE_FOLDER, SUB_FOLDER)

    # Check if the base folder exists
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)

    # Check if the sub folder exists
    if not os.path.exists(path):
        os.makedirs(path)

    # Set up headers for API request
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    # Make the API call
    response = requests.get(
        (
            f"https://api.avito.ru/messenger/v2/accounts/{AVITO_USER_ID}/"
            f"chats?unread_only=true"
        ),
        headers=headers,
    )

    # Check the response status
    if response.status_code == 200:
        # Iterate through each message in the response
        for message in response.json()["chats"]:
            try:
                chat_id = message["id"]
                message_content = message["last_message"]["content"]["text"]
                # Send message to user only in regular mode
                if not args.dry:
                    result = generate_chatgpt_answer(
                        user_id=chat_id,
                        prompt=message_content,
                        engine="avito",
                    )
                    # send_message_back(result, chat_id)
                    logging.info((f"GPT Message: ->  {result}"))
                else:
                    result = generate_chatgpt_answer(
                        user_id=chat_id,
                        prompt=message_content,
                        engine="avito",
                    )
                    logging.info((f"GPT Message: ->  {result}"))
            except Exception as e:
                logging.error(f"Error processing a message: {e}")

    # If token gets expired (403 Forbidden)
    elif response.status_code == 403:
        # Handle 403 error by calling  function and call api back
        logging.debug("Need to get token")
        get_access_token()
        get_new_messages()

    else:
        # Log errors for other status codes
        logging.error(
            (
                "API call failed with status code"
                f" {response.status_code}. Error message: {response.text}"
            )
        )


if __name__ == "__main__":
    args = parse_args()

    if args.dry:
        logging.info("Running in dry mode. Performing dry run actions...")
    while True:
        get_new_messages()
        logging.debug("API has been called")
        time.sleep(POLLING_INTERVAL)
