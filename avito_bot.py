import requests
import time
import os
import argparse
import logging
from utils import send_token_error
from message_handler import generate_chatgpt_answer, check_contact_number

# Configure logging
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

AVITO_USER_ID = os.environ["AVITO_USER_ID"]
ACCESS_TOKEN = None
SLEEP_TIME = 10


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

    client_id = os.environ["AVITO_CLIENT_ID"]
    client_secret = os.environ["AVITO_CLIENT_SECRET"]
    grant_type = "client_credentials"  # fixed value

    # Set up headers
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Params
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": grant_type,
    }

    # Make the API call
    response = requests.post(
        "https://api.avito.ru/token", headers=headers, data=data
    )

    if response.status_code == 200:
        # Save the token to token.json in the desired format
        access_token = response.json().get("access_token")
        ACCESS_TOKEN = access_token
    else:
        send_token_error(response.status_code, response.text)
        logging.error("Could not get Token")


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
        logging.info("API call successful.")
    elif response.status_code == 403:
        # Handle 403 error by calling  function and call api back
        logging.warning("Need to get token")
        get_access_token()
        send_message_back(reply_message, chat_id)
    else:
        logging.error(
            f"API call failed with status code {response.status_code}"
        )


def end_conversation(reply_message: str, chat_id: str) -> None:
    """
    Function to end conversation after getting phone number
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
        logging.info("API call successful.")
    elif response.status_code == 403:
        # Handle 403 error by calling  function and call api back
        logging.warning("Need to get token")
        get_access_token()
        send_message_back(reply_message, chat_id)
    else:
        logging.error(
            f"API call failed with status code {response.status_code}"
        )


def dry_run() -> None:
    """
    Actions to perform in dry run mode
    """
    logging.info("Running in dry mode. Performing dry run actions...")
    while True:
        get_new_messages()
        logging.info("API has been called")
        time.sleep(SLEEP_TIME)


def regular_run() -> None:
    """
    Actions to perform in regular mode
    """
    while True:
        get_new_messages()
        logging.info("API has been called")
        time.sleep(SLEEP_TIME)


def get_new_messages():
    """
    Function to get new messages from Avito
    """

    # If access token is None, obtain a new one
    if ACCESS_TOKEN is None:
        get_access_token()

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
                    # Check contact number and in the message
                    phone_status = check_contact_number(message_content)
                    if phone_status:
                        end_message = (
                            "Спасибо, в рабочее время мы с вами свяжемся!"
                        )

                        # end_conversation(end_message)
                        logging.info(
                            (
                                f"Message: -> "
                                f"Messagae sent: -> {end_message}"
                            )
                        )
                    else:
                        # Generate a response from GPT and send it back
                        result = generate_chatgpt_answer(
                            user_id=chat_id,
                            prompt=message_content,
                            engine="avito",
                        )
                        if result.startswith("Error"):
                            logging.error((f"GPT Message Error: -> {result}"))
                            continue

                        # send_message_back(result, chat_id)
                        logging.info(
                            (f"Message: -> " f"Messagae sent: -> {result}")
                        )
                else:
                    # Log message and chat_id in dry run mode
                    logging.info(
                        (f"Dry run mode: -> " f"Message: {message_content}")
                    )
            except Exception as e:
                logging.error(f"Error processing a message: {e}")

    # If token gets expired (403 Forbidden)
    elif response.status_code == 403:
        # Handle 403 error by calling  function and call api back
        logging.warning("Need to get token")
        get_access_token()
        get_new_messages()

    else:
        # Log errors for other status codes
        logging.error(
            f"API call failed with status code {response.status_code}"
        )


if __name__ == "__main__":
    args = parse_args()

    # Check if --dry flag is present
    if args.dry:
        dry_run()
    else:
        regular_run()
