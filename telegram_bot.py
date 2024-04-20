import os
import json
import logging
from database import session_maker
from constants import (
    BASE_FOLDER,
    SUB_FOLDER_TG,
    LOGGING_LEVEL,
    POLLING_INTERVAL,
)
from message_handler import generate_chatgpt_answer
from telebot import types
import telebot
from sqlalchemy.orm import Session
import time
from repository import get_active_telegram_bot_accounts
from dataclasses import dataclass


logging.basicConfig(format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(level=LOGGING_LEVEL)


@dataclass
class BotInfo:
    id: int
    instance: telebot.TeleBot
    prompt: str
    offset: int = 0


def get_bots(session: Session) -> list[BotInfo]:
    """
    Retrieve Telegram bot instances from the database and set bot commands.
    """
    bots = []
    accounts = get_active_telegram_bot_accounts(session)
    for account in accounts:
        bot_instance = telebot.TeleBot(account.token)

        # Set bot commands
        bot_instance.set_my_commands(
            [
                types.BotCommand(command="start", description="Старт бота"),
                types.BotCommand(
                    command="reset", description="Сбросить историю чата"
                ),
            ]
        )

        bot_info = BotInfo(
            id=account.id,
            instance=bot_instance,
            prompt=account.prompt.text,
        )
        bots.append(bot_info)
    return bots


def force_private(message: telebot.types.Message) -> bool:
    """
    Function to force chat into private chat
    """
    if message.chat.type == "private":
        return True
    return False


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


def reset_command_handler(
    message: telebot.types.Message, bot: BotInfo
) -> None:
    """
    Function to handle /history command
    """
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"

    # Clear history
    with open(
        f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{bot.id}/{user_id}/history.json", "w"
    ) as file:
        json.dump([], file)

    # Send message to user
    bot.instance.send_chat_action(chat_id=message.chat.id, action="typing")
    bot.instance.reply_to(message=message, text="История очищена")


def start_command_handler(
    message: telebot.types.Message, bot: BotInfo
) -> None:
    """
    Function to handle /start command
    """
    instance = bot.instance
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"

    user_folder = f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{bot.id}/{user_id}"
    if os.path.exists(user_folder):
        # Send welcome back message to existing user
        instance.send_chat_action(chat_id=message.chat.id, action="typing")
        instance.reply_to(
            message=message,
            text=(
                f"Привет {message.from_user.first_name}.\nНапиши сообщение,"
                " чтобы начать диалог!\n\nКоманды:\n/reset: Сбросить историю"
                " чата и начать новый диалог"
            ),
        )

    else:
        # Create user account for new member
        os.makedirs(
            user_folder, exist_ok=True
        )  # Create directory if it doesn't exist
        with open(f"{user_folder}/history.json", "w") as file:
            json.dump([], file)

        # Send welcome back message to existing user
        instance.send_chat_action(chat_id=message.chat.id, action="typing")
        instance.reply_to(
            message=message,
            text=(
                f"Привет {message.from_user.first_name}.\nНапиши сообщение,"
                " чтобы начать диалог!\n\nКоманды:\n/reset: Сбросить историю"
                " чата и начать новый диалог"
            ),
        )


def handle_messages(message: telebot.types.Message, bot: BotInfo) -> None:
    """
    Function to handle all text messages
    """
    instance = bot.instance
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"
    user_prompt = message.text.strip()

    if (
        message.reply_to_message
        and message.reply_to_message.from_user.id == instance.get_me().id
    ):
        try:
            instance.send_chat_action(chat_id=message.chat.id, action="typing")
            gpt_prompt = instance.reply_to(
                message=message,
                text="Думаю над ответом\.\.\.",
                parse_mode="MarkdownV2",
            )

            result = generate_chatgpt_answer(
                user_id=user_id,
                message=user_prompt,
                engine=SUB_FOLDER_TG,
                chat=bot.id,
                system_prompt=bot.prompt,
            )

            instance.edit_message_text(
                chat_id=message.chat.id,
                message_id=gpt_prompt.message_id,
                text=escape_markdown(result),
                parse_mode="MarkdownV2",
            )
        except Exception:
            logger.exception("Error sending tg message")

    elif force_private(message):
        try:
            instance.send_chat_action(chat_id=message.chat.id, action="typing")
            gpt_prompt = instance.reply_to(
                message=message,
                text="Думаю над ответом\.\.\.",
                parse_mode="MarkdownV2",
            )

            result = generate_chatgpt_answer(
                user_id=user_id,
                message=user_prompt,
                engine=SUB_FOLDER_TG,
                chat=bot.id,
                system_prompt=bot.prompt,
            )
            result = "[Empty Result]" if not result else result

            instance.edit_message_text(
                chat_id=message.chat.id,
                message_id=gpt_prompt.message_id,
                text=escape_markdown(result),
                parse_mode="MarkdownV2",
            )
        except Exception:
            logger.exception("Error sending tg message")


COMMANDS_HANDLERS = {
    "/start": start_command_handler,
    "/reset": reset_command_handler,
}


def start_bot():
    # Initialize last_update_ids dict
    last_update_ids = {bot.id: 0 for bot in get_bots(session_maker())}
    while True:
        with session_maker() as session:
            bots = get_bots(session)
            bots_count = len(bots)

            # check if new bot is added to temp dict or not
            for bot_info in bots:
                if bot_info.id not in last_update_ids:
                    last_update_ids[bot_info.id] = 0

            for bot_info in bots:
                bot_instance = bot_info.instance
                last_update_id = last_update_ids[bot_info.id]
                updates = bot_instance.get_updates(offset=last_update_id + 1)

                for update in updates:
                    message = update.message
                    if message and message.content_type == "text":
                        last_update_ids[bot_info.id] = update.update_id
                        command_handler = COMMANDS_HANDLERS.get(
                            message.text.strip()
                        )
                        handler = command_handler or handle_messages
                        handler(message, bot_info)
                    else:
                        logger.warning("Non-text message received")

                time.sleep(max(POLLING_INTERVAL / bots_count, 1))


if __name__ == "__main__":
    path = os.path.join(BASE_FOLDER, SUB_FOLDER_TG)
    # Check if the base folder exists
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)

    # Check if the sub folder exists
    if not os.path.exists(path):
        os.makedirs(path)
    start_bot()
