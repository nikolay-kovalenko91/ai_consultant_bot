import telebot
import threading
import os
import json
import logging
from database import session_maker, TelegramAccounts
from constants import BASE_FOLDER, SUB_FOLDER_TG, LOGGING_LEVEL
from message_handler import generate_chatgpt_answer
from repository import get_account_prompts
from telebot import types

logging.basicConfig(format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(level=LOGGING_LEVEL)


def get_bots() -> list:
    """
    Retrieve Telegram bot instances from the database and set bot commands.
    """
    bots = []
    with session_maker() as session:
        accounts = session.query(TelegramAccounts).all()
        for account in accounts:
            bot = {}
            prompt = get_account_prompts(account.id, session)
            bot["id"] = account.id
            bot["instance"] = telebot.TeleBot(account.token)
            bot["prompt"] = prompt

            # Set bot commands
            bot["instance"].set_my_commands(
                [
                    types.BotCommand(
                        command="start", description="Старт бота"
                    ),
                    types.BotCommand(
                        command="reset", description="Сбросить историю чата"
                    ),
                ]
            )

            bots.append(bot)
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


def gpt_command_handler(message: telebot.types.Message, bot: dict) -> None:
    """
    Function to handle /history command
    """
    INNER = bot["id"]
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"

    # Clear history
    with open(
        f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{INNER}/{user_id}/history.json", "w"
    ) as file:
        json.dump([], file)

    # Send message to user
    bot["instance"].send_chat_action(chat_id=message.chat.id, action="typing")
    bot["instance"].reply_to(message=message, text="История очищена")


def start_command_handler(
    message: telebot.types.Message, instance: dict
) -> None:
    """
    Function to handle /start command
    """
    bot = instance["instance"]
    user_id = f"{message.from_user.first_name}_{message.from_user.id}"

    INNER = instance["id"]
    user_folder = f"{BASE_FOLDER}/{SUB_FOLDER_TG}/{INNER}/{user_id}"
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
    bot = instance["instance"]
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
                chat=instance["id"],
                system_prompt=instance["prompt"],
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
                chat=instance["id"],
                system_prompt=instance["prompt"],
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


def connect_bot(bot_instance: dict) -> None:
    """
    Function to connect to Telegram bot instance and handle messages.
    """
    last_update_id = 0
    while True:
        updates = bot_instance["instance"].get_updates(
            offset=last_update_id + 1
        )
        for update in updates:
            message = update.message
            if message is not None and message.content_type == "text":
                last_update_id = update.update_id
                if message.text == "/start":
                    start_command_handler(message, bot_instance)
                elif message.text == "/reset":
                    gpt_command_handler(message, bot_instance)
                else:
                    handle_messages(message, bot_instance)
            else:
                # if sent message is not text it will be passed
                logger.warning("Non text message recieved")
                pass


def create_threads(bots: list) -> list:
    """
    Function to create and start threads for each Telegram bot instance.
    """
    threads = []
    for bot in bots:
        thread = threading.Thread(target=connect_bot, args=(bot,))
        threads.append(thread)
        thread.start()
    return threads


def main() -> None:
    """
    Main function to start the Telegram bot threads.
    """
    # Retrieve Telegram bot instances
    bots = get_bots()

    # Create and start threads for each Telegram bot instance
    threads = create_threads(bots)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
