import json
import os

import telebot
import logging

from message_handler import generate_chatgpt_answer
from constants import (
    TELEGRAM_BOT_TOKEN,
    POLLING_INTERVAL,
    BASE_FOLDER,
    SUB_FOLDER_TG,
    LOGGING_LEVEL,
)

logging.basicConfig(format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(level=LOGGING_LEVEL)

Bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


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


@Bot.message_handler(commands=["start"])
def start_command_handler(message: callable) -> None:
    """
    Function to handle /start command
    """

    user_id = f"{message.from_user.first_name}_{message.from_user.id}"

    # Check if the user account exists
    if os.path.exists(f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{user_id}"):
        # Send welcome back message to existing user
        Bot.send_chat_action(chat_id=message.chat.id, action="typing")
        Bot.reply_to(
            message=message,
            text=(
                f"Привет {message.from_user.first_name}.\nНапиши сообщение,"
                " чтобы начать диалог!\n\nКоманды:\n/reset: Сбросить историю"
                " чата и начать новый диалог"
            ),
        )

    else:
        # Create user account for new member
        os.mkdir(f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{user_id}")
        with open(
            f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{user_id}/history.json", "w"
        ) as file:
            json.dump([], file)

        # Send welcome back message to existing user
        Bot.send_chat_action(chat_id=message.chat.id, action="typing")
        Bot.reply_to(
            message=message,
            text=(
                f"Привет {message.from_user.first_name}.\nНапиши сообщение,"
                " чтобы начать диалог!\n\nКоманды:\n/reset: Сбросить историю"
                " чата и начать новый диалог"
            ),
        )


@Bot.message_handler(commands=["reset"])
def gpt_command_handler(message: callable) -> None:
    """
    Function to handle /history command
    """

    # User ID
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"

    # Clear history
    with open(
        f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{user_id}/history.json", "w"
    ) as file:
        json.dump([], file)

    # Send message to user
    Bot.send_chat_action(chat_id=message.chat.id, action="typing")
    Bot.reply_to(message=message, text="История очищена")


@Bot.message_handler(content_types=["text"])
def handle_messages(message: callable) -> None:
    """
    Function to handle all text messages
    """

    # User ID
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"

    # Gets user input
    user_prompt = message.text.strip()

    # Avoid making mess for replying in groups
    if (
        message.reply_to_message
        and message.reply_to_message.from_user.id == Bot.get_me().id
    ):
        try:
            # Send waiting message
            Bot.send_chat_action(chat_id=message.chat.id, action="typing")
            gpt_prompt = Bot.reply_to(
                message=message,
                text="Думаю над ответом\.\.\.",
                parse_mode="MarkdownV2",
            )

            # Fetch results from function
            result = generate_chatgpt_answer(
                user_id=user_id, message=user_prompt, engine=SUB_FOLDER_TG
            )

            # Edit waiting message and answer user message
            Bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=gpt_prompt.message_id,
                text=escape_markdown(result),
                parse_mode="MarkdownV2",
            )
        except Exception:
            logger.exception("Error sending tg message")

    # Handle private chat
    elif force_private(message):
        try:
            # Send waiting message
            Bot.send_chat_action(chat_id=message.chat.id, action="typing")
            gpt_prompt = Bot.reply_to(
                message=message,
                text="Думаю над ответом\.\.\.",
                parse_mode="MarkdownV2",
            )

            # Fetch results from function
            result = generate_chatgpt_answer(
                user_id=user_id, message=user_prompt, engine=SUB_FOLDER_TG
            )
            result = "[Empty Result]" if not result else result

            # Answer user message
            Bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=gpt_prompt.message_id,
                text=escape_markdown(result),
                parse_mode="MarkdownV2",
            )
        except Exception:
            logger.exception("Error sending tg message")


# Connect to bot
if __name__ == "__main__":
    path = os.path.join(BASE_FOLDER, SUB_FOLDER_TG)
    # Check if the base folder exists
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)

    # Check if the sub folder exists
    if not os.path.exists(path):
        os.makedirs(path)

    try:
        Bot.polling(interval=POLLING_INTERVAL)
    except Exception:
        logger.exception("Error sending tg message")
