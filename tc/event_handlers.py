import logging

from database import session_maker
from message_handler import generate_chatgpt_answer
from tc.tc_repository import get_prompt_data, get_account_data
from tc.tc_client_model import ClientModel
from tc.tc_constants import TC_SESSIONS_DIRECTORY, TCEngine, State, TypeMessage
from tc.tc_telegram_json import TelegramJSON

telegram_json = TelegramJSON()


def authorization_event_handle(client: ClientModel, event):
    client_id = client.client_id
    phone = client.phone

    auth_state = event["authorization_state"]
    if auth_state["@type"] == "authorizationStateWaitTdlibParameters":
        telegram_json.send_parameters(
            client_id,
            db_path=f"{TC_SESSIONS_DIRECTORY}/{phone}",
            api_id=client.api_id,
            api_hash=client.api_hash,
        )

    if auth_state["@type"] == "authorizationStateWaitEncryptionKey":
        telegram_json.td_json_client_send(
            client_id,
            {"@type": "checkDatabaseEncryptionKey", "encryption_key": ""},
        )

    if auth_state["@type"] == "authorizationStateWaitPhoneNumber":
        telegram_json.send_phone(client_id, phone)

    if auth_state["@type"] == "authorizationStateWaitCode":
        code = input("Введите код: ")
        telegram_json.send_code(client_id, code)

    if auth_state["@type"] == "authorizationStateWaitPassword":
        password = input("Введите пароль: ")
        telegram_json.send_password(client_id, password)

    if auth_state["@type"] == "authorizationStateReady":
        logging.info(f"Аккаунт {phone} успешно авторизован")
        telegram_json.get_me(client_id)

    if auth_state["@type"] == "authorizationStateLoggingOut":
        logging.info(f"Сессия аккаунта {phone} завершена")


def user_event_handle(client: ClientModel, event):
    extra = event.get("@extra")
    if extra and extra.get("type") == "getMe":
        client.telegram_user_id = event.get("id")
        return {"result": State.Authorization.READY, "client": client}


def error_event_handle(client: ClientModel, event):
    logging.warning(f"{client.phone}: {event}")
    client_id = client.client_id
    if event.get("message") == TypeMessage.Error.PHONE_CODE_INVALID:
        code = input("Неверный код. Введите код повторно: ")
        telegram_json.send_code(client_id, code)
    elif event.get("message") == TypeMessage.Error.PASSWORD_HASH_INVALID:
        password = input("Неверный пароль. Введите пароль повторно: ")
        telegram_json.send_password(client_id, password)
    elif event.get("message") == TypeMessage.Error.PHONE_CODE_EXPIRED:
        return {
            "result": TypeMessage.Error.PHONE_CODE_EXPIRED,
            "client": client,
        }

    elif TypeMessage.Error.LOCK_FILE in event.get("message"):
        return TypeMessage.Error.LOCK_FILE


def update_new_messages_handle(client: ClientModel, event):
    message_id = event.get("message").get("id")
    chat_id = event.get("message").get("chat_id")
    text = event.get("message").get("content").get("text")
    caption = event.get("message").get("content").get("caption")
    text = caption if not text else text

    is_channel_post = event.get("message").get("is_channel_post")

    sender_user_id = event.get("message").get("sender_id").get("user_id")

    logging.info(f"{client.phone}: {chat_id}_{sender_user_id} -> {text}")

    if (
        text
        and not is_channel_post
        and sender_user_id != client.telegram_user_id
    ):
        text = text.get("text")

        with session_maker() as session:
            account = get_account_data(session, client.telegram_user_id)

            answer = None

            # group message
            if chat_id != sender_user_id:
                if account.keywords:
                    keywords = [
                        word.strip().lower()
                        for word in account.keywords.split(",")
                        if word.strip()
                    ]
                    if any(keyword in text.lower() for keyword in keywords):
                        prompt = get_prompt_data(
                            session, account.group_message_prompt_id
                        )
                        if prompt:
                            # answer = prompt
                            answer = generate_chatgpt_answer(
                                user_id=sender_user_id,
                                message=text,
                                engine=TCEngine.GROUP_MESSAGE,
                                system_prompt=prompt,
                            )

            # private message
            else:
                prompt = get_prompt_data(
                    session, account.private_message_prompt_id
                )
                if prompt:
                    # answer = prompt
                    answer = generate_chatgpt_answer(
                        user_id=sender_user_id,
                        message=text,
                        engine=TCEngine.PRIVATE_MESSAGE,
                        system_prompt=prompt,
                    )

            if answer:
                telegram_json.send_text_message(
                    client_id=client.client_id,
                    chat_id=chat_id,
                    text=answer,
                    reply_to_message_id=message_id
                    if chat_id != sender_user_id
                    else 0,
                )
