import argparse
import logging

import os
import random
import time
from typing import Iterable, Type

import requests
from sqlalchemy.orm import Session

from constants import (
    BASE_FOLDER,
    SUB_FOLDER_AVITO,
    POLLING_INTERVAL,
    BREAK_TIME,
    LOGGING_LEVEL,
)
from database import AvitoAccounts, session_maker
from message_handler import generate_chatgpt_answer, handle_nontext_message
from repository import get_active_avito_accounts
from utils import generate_gpt_prompt

access_tokens: dict[str, str] = dict()

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


def get_access_token(account: AvitoAccounts) -> None:
    """
    Function to get new access token
    """

    # Set up headers
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Params
    data = {
        "client_id": account.client_id,
        "client_secret": account.client_secret,
        "grant_type": "client_credentials",
    }

    # Make the API call
    response = requests.post(
        "https://api.avito.ru/token", headers=headers, data=data
    )

    if response.status_code == 200:
        # Save the token to token.json in the desired format
        access_token = response.json().get("access_token")
        access_tokens[account.user_id] = access_token
    else:
        logger.error(f"Token error : {response.status_code}, {response.text}")


def send_message_back(
        account: AvitoAccounts, reply_message: str,
        chat_id: str, retry=True,
) -> None:
    """
    Function to send message back to user
    """

    # Set up headers
    headers = {
        "Authorization": f"Bearer {access_tokens.get(account.user_id)}",
        "Content-Type": "application/json",
    }

    # Prepare the payload
    payload = {"message": {"text": reply_message}, "type": "text"}

    # Make the API call
    response = requests.post(
        (
            f"https://api.avito.ru/messenger/v1/accounts/{account.user_id}/"
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
        get_access_token(account)
        send_message_back(reply_message, chat_id, retry=False)
    else:
        logger.error(
            f"Send message back is failed. Status:{response.status_code}. "
            f"Error: {response.text}. Payload: {payload}"
        )


def read_message(account: AvitoAccounts, chat_id: str, retry=True) -> None:
    """
    Function to make message to be read
    """
    # Set up headers for API request
    headers = {"Authorization": f"Bearer {access_tokens.get(account.user_id)}"}

    response = requests.post(
        (
            f"https://api.avito.ru/messenger/v1/accounts/{account.user_id}/"
            f"chats/{chat_id}/read"
        ),
        headers=headers,
    )
    if response.status_code == 200:
        logger.debug(f"Message from {chat_id=} has been read")
    elif response.status_code == 403 and retry:
        # Handle 403 error by calling  function and call api back
        logger.debug("Need to get auth token")
        get_access_token(account)
        read_message(chat_id, retry=False)
    else:
        logger.error(
            f"Read message is failed. Status:{response.status_code}. "
            f"Error: {response.text}"
        )


def get_new_messages(session: Session, account: AvitoAccounts, retry=True) -> None:
    """
    Function to get new messages from Avito
    """

    # Set up headers for API request
    headers = {"Authorization": f"Bearer {access_tokens.get(account.user_id)}"}

    # Make the API call
    response = requests.get(
        (
            f"https://api.avito.ru/messenger/v2/accounts/{account.user_id}/"
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
                        system_prompt=generate_gpt_prompt(session, account),
                    )
                    if not args.dry:
                        send_message_back(account, result, chat_id, retry=True)
                        time.sleep(BREAK_TIME)
                    logger.debug(
                        f"Got message={message_content['content']}'; "
                        f"GPT answer={result}"
                    )
                else:
                    if not args.dry:
                        handle_nontext_message(
                            user_id=chat_id,
                            engine=SUB_FOLDER_AVITO,
                            system_prompt=generate_gpt_prompt(session, account),
                        )
                        read_message(account, chat_id, retry=True)
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
        get_access_token(account)
        get_new_messages(session, account, retry=False)

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
        with session_maker() as session:
            for account in get_active_avito_accounts(session):
                get_new_messages(session, account, retry=True)

        time.sleep(POLLING_INTERVAL)
