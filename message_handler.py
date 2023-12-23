import os
import openai
import json
import re
from utils import send_contact, send_email
from constants import (
    OPENAI_API_KEY,
    CLOSING_MESSAGE,
    SYSTEM_PROMPT,
    BASE_FOLDER,
    EMAIL_RECEIVER,
    NON_TEXT_EMAIL_MESSAGE_BODY,
    NON_TEXT_EMAIL_MESSAGE_SUBJECT,
)
import logging
from typing import List, Dict
import time


logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


openai.api_key = OPENAI_API_KEY


def check_contact_number(text: str) -> bool:
    # Validaiton for  phone number format
    patterns = [
        # +7(123)456-78-90
        r"\+(\d{1,2})\((\d{3})\)(\d{3}-\d{2}-\d{2})",
        # +7 (123) 456-78-90
        r"\+(\d{1,2})\s?\((\d{3})\)\s?(\d{3}-\d{2}-\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # If phone is matched to validation, send it to email
            send_contact(match.group(0))
            return True

    return False


def get_or_create_history(user_id: str, engine: str):
    """
    Get existing chat history or create a new one if not exists
    """
    folder_path = f"{BASE_FOLDER}/{engine}/{user_id}"
    file_path = f"{folder_path}/history.json"

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            json.dump([], file)

    with open(file_path, "r") as file:
        history = json.load(file)

    if len(history) == 0:
        history.append({"role": "system", "content": SYSTEM_PROMPT})

    return file_path, history


def handle_nontext_message(user_id: str, engine: str) -> None:
    """
    Gets last message from chat history and sends to manager
    """
    # Make sure user have account, even if it not started bot.
    file_path, history = get_or_create_history(user_id, engine)

    last_gpt_message = None
    for message in reversed(history):
        if message["role"] == "assistant":
            last_gpt_message = message["content"]

    send_email(
        EMAIL_RECEIVER,
        NON_TEXT_EMAIL_MESSAGE_SUBJECT,
        f"{NON_TEXT_EMAIL_MESSAGE_BODY} {last_gpt_message}",
    )


def get_chat_completion(history: List[Dict[str, str]]) -> str:
    """
    Generates a chat completion using the OpenAI API
    """
    # completion = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=history,
    # )
    # logging.debug(
    #     f'{completion["usage"]["prompt_tokens"]} prompt tokens counted by'
    #     " the OpenAI API."
    # )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=history,
        )
    except openai.error.RateLimitError:
        time.sleep(30)
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=history,
        )
    except openai.error.InvalidRequestError as e:
        logging.error(f"ChatGPT Invalid request error: {e}")
        return "Мы ответим вам как можно скорее"
    logging.debug(
        f'{completion["usage"]["prompt_tokens"]} prompt tokens counted by'
        " the OpenAI API."
    )

    return completion.choices[0].message.content


def generate_chatgpt_answer(user_id: str, prompt: str, engine: str) -> str:
    """
    Chat GPT function
    """

    # try:
    # Make sure user have account, even if it not started bot.
    file_path, history = get_or_create_history(user_id, engine)

    history.append({"role": "user", "content": prompt})

    # Check if text is valid phone number or not
    if check_contact_number(prompt):
        history.append({"role": "assistant", "content": CLOSING_MESSAGE})
        with open(file_path, "w") as file:
            json.dump(history, file, indent=2, ensure_ascii=False)
        return CLOSING_MESSAGE

    # Else case text will be sent to GPT
    gpt_result = get_chat_completion(history)
    # Add GPT prompt to history
    history.append({"role": "assistant", "content": gpt_result})

    # Save new history
    with open(file_path, "w") as file:
        json.dump(history, file, indent=2, ensure_ascii=False)

    # Return chat answer
    return gpt_result
