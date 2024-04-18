import os
import json
import logging
from database import session_maker, TelegramAccount
from constants import (
    BASE_FOLDER,
    SUB_FOLDER_TG,
    LOGGING_LEVEL,
    POLLING_INTERVAL,
)
from message_handler import generate_chatgpt_answer
from telebot import types
import telebot
from sqlalchemy.orm import joinedload
import time
from schema import BotInfo

logging.basicConfig(format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(level=LOGGING_LEVEL)


def get_bots() -> list[BotInfo]:
    """
    Retrieve Telegram bot instances from the database and set bot commands.
    """
    bots = []
    with session_maker() as session:
        accounts = (
            session.query(TelegramAccount)
            .options(joinedload(TelegramAccount.prompt))
            .all()
        )

        for account in accounts:
            prompt = account.prompt.text

            bot_instance = telebot.TeleBot(account.token)

            # Set bot commands
            bot_instance.set_my_commands(
                [
                    types.BotCommand(
                        command="start", description="Старт бота"
                    ),
                    types.BotCommand(
                        command="reset", description="Сбросить историю чата"
                    ),
                ]
            )

            bot_info = BotInfo(
                id=account.id, instance=bot_instance, prompt=prompt
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


def reset_command_handler(message: telebot.types.Message, bot: dict) -> None:
    """
    Function to handle /history command
    """
    BOT_ID = bot.id
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"

    # Clear history
    with open(
        f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{BOT_ID}/{user_id}/history.json", "w"
    ) as file:
        json.dump([], file)

    # Send message to user
    bot.instance.send_chat_action(chat_id=message.chat.id, action="typing")
    bot.instance.reply_to(message=message, text="История очищена")


def start_command_handler(message: telebot.types.Message, instance) -> None:
    """
    Function to handle /start command
    """
    bot = instance.instance
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"

    BOT_ID = instance.id
    user_folder = f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{BOT_ID}/{user_id}"
    if os.path.exists(user_folder):
        # Send welcome back message to existing user
        bot.send_chat_action(chat_id=message.chat.id, action="typing")
        bot.reply_to(
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
        bot.send_chat_action(chat_id=message.chat.id, action="typing")
        bot.reply_to(
            message=message,
            text=(
                f"Привет {message.from_user.first_name}.\nНапиши сообщение,"
                " чтобы начать диалог!\n\nКоманды:\n/reset: Сбросить историю"
                " чата и начать новый диалог"
            ),
        )


def handle_messages(message: telebot.types.Message, instance: dict) -> None:
    """
    Function to handle all text messages
    """
    bot = instance.instance
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"
    user_prompt = message.text.strip()

    if (
        message.reply_to_message
        and message.reply_to_message.from_user.id == bot.get_me().id
    ):
        try:
            bot.send_chat_action(chat_id=message.chat.id, action="typing")
            gpt_prompt = bot.reply_to(
                message=message,
                text="Думаю над ответом\.\.\.",
                parse_mode="MarkdownV2",
            )

            result = generate_chatgpt_answer(
                user_id=user_id,
                message=user_prompt,
                engine=SUB_FOLDER_TG,
                chat=instance.id,
                system_prompt=instance.prompt,
            )

            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=gpt_prompt.message_id,
                text=escape_markdown(result),
                parse_mode="MarkdownV2",
            )
        except Exception:
            logger.exception("Error sending tg message")

    elif force_private(message):
        try:
            bot.send_chat_action(chat_id=message.chat.id, action="typing")
            gpt_prompt = bot.reply_to(
                message=message,
                text="Думаю над ответом\.\.\.",
                parse_mode="MarkdownV2",
            )

            result = generate_chatgpt_answer(
                user_id=user_id,
                message=user_prompt,
                engine=SUB_FOLDER_TG,
                chat=instance.id,
                system_prompt=instance.prompt,
            )
            result = "[Empty Result]" if not result else result

            bot.edit_message_text(
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
    # Initialize the last_update_ids dict
    last_update_ids = {bot_info.id: 0 for bot_info in get_bots()}
    while True:
        bots = get_bots()
        bots_count = len(bots)

        for bot_info in bots:
            bot_instance = bot_info.instance

            # Get the last_update_id for this bot
            last_update_id = last_update_ids[bot_info.id]
            updates = bot_instance.get_updates(offset=last_update_id + 1)

            for update in updates:
                message = update.message
                if message is not None and message.content_type == "text":
                    # Update the last_update_id for this bot
                    last_update_ids[bot_info.id] = update.update_id
                    command_handler = COMMANDS_HANDLERS.get(
                        message.text.strip()
                    )
                    if command_handler:
                        command_handler(message, bot_info)
                    else:
                        handle_messages(message, bot_info)
                else:
                    # if sent message is not text it will be passed
                    logger.warning("Non text message received")
            time.sleep(max(POLLING_INTERVAL / bots_count, 1))


if __name__ == "__main__":
    start_bot()
