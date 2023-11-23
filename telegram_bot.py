import json
import os

import telebot

from message_handler import generate_chatgpt_answer, check_contact_number


Bot = telebot.TeleBot(os.environ["BOT_TOKEN"])
print(f"The Bot is online (id: {Bot.get_me().id})...")


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
    if os.path.exists(f"history/telegram/{user_id}"):
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
        os.mkdir(f"history/telegram/{user_id}")
        with open(f"history/telegram/{user_id}/history.json", "w") as file:
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
    with open(f"history/telegram/{user_id}/history.json", "w") as file:
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
        # Send waiting message
        Bot.send_chat_action(chat_id=message.chat.id, action="typing")
        gpt_prompt = Bot.reply_to(
            message=message,
            text="Думаю над ответом\.\.\.",
            parse_mode="MarkdownV2",
        )

        # Pass sent message through check phone number function
        phone_status = check_contact_number(user_prompt)

        # If message is phone number end conversation, else send message to GPT
        if phone_status:
            Bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=gpt_prompt.message_id,
                text="Спасибо, в рабочее время мы с вами свяжемся!\.\.\.",
                parse_mode="MarkdownV2",
            )

        else:
            # Fetch results from function
            result = generate_chatgpt_answer(
                user_id=user_id, prompt=user_prompt, engine="telegram"
            )

            # Edit waiting message and answer user message
            Bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=gpt_prompt.message_id,
                text=escape_markdown(result),
                parse_mode="MarkdownV2",
            )

    # Handle private chat
    elif force_private(message):
        # Send waiting message
        Bot.send_chat_action(chat_id=message.chat.id, action="typing")
        gpt_prompt = Bot.reply_to(
            message=message,
            text="Думаю над ответом\.\.\.",
            parse_mode="MarkdownV2",
        )

        # Pass sent message through check phone number function
        phone_status = check_contact_number(user_prompt)

        # If message is phone number end conversation, else send message to GPT
        if phone_status:
            Bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=gpt_prompt.message_id,
                text="Спасибо, в рабочее время мы с вами свяжемся!\.\.\.",
                parse_mode="MarkdownV2",
            )
        else:
            # Fetch results from function
            result = generate_chatgpt_answer(
                user_id=user_id, prompt=user_prompt, engine="telegram"
            )
            result = "[Empty Result]" if not result else result

            # Answer user message
            Bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=gpt_prompt.message_id,
                text=escape_markdown(result),
                parse_mode="MarkdownV2",
            )


# Connect to bot
if __name__ == "__main__":
    try:
        Bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception:
        print("Lost connection!")
