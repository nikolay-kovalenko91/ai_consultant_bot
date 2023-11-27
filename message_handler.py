import os
import openai
import json
import re
from utils import send_contact

openai.api_key = os.environ["OPENAI_API_KEY"]


def generate_chatgpt_answer(user_id: int, prompt: str, engine: str) -> str:
    """
    Chat GPT function
    """

    try:
        # Make sure user have account, even if it not started bot.
        folder_path = f"history/{engine}/{user_id}"
        file_path = f"history/{engine}/{user_id}/history.json"

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
    except Exception:
        raise
        # print(f"Error due to {ex}")


def check_contact_number(text: str):
    # Validaiton for  phone number format
    patterns = [
        r"\+(\d{1,2})\((\d{3})\)(\d{3}-\d{2}-\d{2})",  # +7(123)456-78-90
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # If phone is matched to validation, send it to email
            send_contact(match.group(0))
            return True

    return False
