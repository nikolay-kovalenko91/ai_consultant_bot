import openai
import json
import os

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
