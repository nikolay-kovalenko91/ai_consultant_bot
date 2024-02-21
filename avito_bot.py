import argparse
import logging

import os
import random
import time
from typing import Iterable, Type

import requests

from constants import (
    CLIENT_ID,
    CLIENT_SECRET,
    AVITO_USER_ID,
    BASE_FOLDER,
    SUB_FOLDER_AVITO,
    POLLING_INTERVAL,
    BREAK_TIME,
    LOGGING_LEVEL,
)
from message_handler import generate_chatgpt_answer, handle_nontext_message


ACCESS_TOKEN = None

logging.basicConfig(format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(level=LOGGING_LEVEL)


def backoff_decorator(
    exceptions: Iterable[Type[Exception]] = (Exception,),
    max_retries: int = 4,
    backoff_seconds: float = 1.0,
):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"Request failed; {e=}. Retrying...")
                    retries += 1
                    sleep = backoff_seconds * 2**retries + random.uniform(
                        0, 1
                    )
                    time.sleep(sleep)
            raise ConnectionError(
                f"{max_retries=} reached. Unable to make the request"
            )

        return wrapper

    return decorator


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
        "grant_type": "client_credentials",
    }

    # Make the API call
    response = requests.post(
        "https://api.avito.ru/token", headers=headers, data=data
    )

    if response.status_code == 200:
        # Save the token to token.json in the desired format
        ACCESS_TOKEN = response.json().get("access_token")
    else:
        logger.error(f"Token error : {response.status_code}, {response.text}")


def send_message_back(reply_message: str, chat_id: str, retry=True) -> None:
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
        logger.debug(f"Message from {chat_id=} successfully answered")
    elif response.status_code == 403 and retry:
        # Handle 403 error by calling  function and call api back
        logger.debug("Need to get auth token")
        get_access_token()
        send_message_back(reply_message, chat_id, retry=False)
    else:
        logger.error(
            f"Send message back is failed. Status:{response.status_code}. "
            f"Error: {response.text}. Payload: {payload}"
        )


def read_message(chat_id: str, retry=True) -> None:
    """
    Function to make message to be read
    """

    # If access token is none get new one
    if ACCESS_TOKEN is None:
        get_access_token()

    # Set up headers for API request
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    response = requests.post(
        (
            f"https://api.avito.ru/messenger/v1/accounts/{AVITO_USER_ID}/"
            f"chats/{chat_id}/read"
        ),
        headers=headers,
    )
    if response.status_code == 200:
        logger.debug(f"Message from {chat_id=} has been read")
    elif response.status_code == 403 and retry:
        # Handle 403 error by calling  function and call api back
        logger.debug("Need to get auth token")
        get_access_token()
        read_message(chat_id, retry=False)
    else:
        logger.error(
            f"Read message is failed. Status:{response.status_code}. "
            f"Error: {response.text}"
        )


def get_new_messages(retry=True):
    """
    Function to get new messages from Avito
    """

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
        messages = response.json()["chats"]
        logger.info(f"Fetched {len(messages)} messages from Avito...")
        for message in messages:
            try:
                chat_id = message["id"]
                message_content = message["last_message"]
                message_type = message_content["type"]

                if message_type == "text" or message_type == "system":
                    # Send message to user only in regular mode
                    result = generate_chatgpt_answer(
                        user_id=chat_id,
                        message=message_content["content"]["text"],
                        engine=SUB_FOLDER_AVITO,
                    )
                    if not args.dry:
                        send_message_back(result, chat_id, retry=True)
                        time.sleep(BREAK_TIME)
                    logger.debug(
                        f"Got message={message_content['content']}'; "
                        f"GPT answer={result}"
                    )
                else:
                    if not args.dry:
                        handle_nontext_message(
                            user_id=chat_id, engine=SUB_FOLDER_AVITO
                        )
                        read_message(chat_id, retry=True)
                    logger.warning(
                        f"Got non-text message from chat ->'{chat_id}'"
                    )
            except Exception:
                logger.exception(
                    "Error occured in proccess: " f"message:{message}"
                )

    # If token gets expired (403 Forbidden)
    elif response.status_code == 403 and retry:
        # Handle 403 error by calling  function and call api back
        logger.debug("Need to get auth token")
        get_access_token()
        get_new_messages(retry=False)

    else:
        # Log errors for other status codes
        logger.error(
            "Get new messages call failed with status code"
            f" {response.status_code}. Error message: {response.text}"
        )


if __name__ == "__main__":
    path = os.path.join(BASE_FOLDER, SUB_FOLDER_AVITO)
    # Check if the base folder exists
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)

    # Check if the sub folder exists
    if not os.path.exists(path):
        os.makedirs(path)

    logger.debug("Starting bot...")
    args = parse_args()
    if args.dry:
        logger.info("Running in dry mode. Performing dry run actions...")
    while True:
        get_new_messages(retry=True)
        time.sleep(POLLING_INTERVAL)
