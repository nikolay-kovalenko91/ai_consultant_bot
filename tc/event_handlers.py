import logging
from typing import Optional, Dict, Any

from constants import TC_SESSIONS_DIRECTORY
from database import session_maker
from tc.messages import create_group_message, create_private_message
from tc.repository import get_account_data
from tc.dataclasses import ClientModel, State, TypeMessage
from tc.telegram_json import TelegramJSON

telegram_json = TelegramJSON()


def authorization_event_handle(
    client: ClientModel, event: Dict[str, Any]
) -> None:
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


def user_event_handle(
    client: ClientModel, event: Dict[str, Any]
) -> Optional[dict]:
    extra = event.get("@extra")
    if extra and extra.get("type") == "getMe":
        client.telegram_user_id = event.get("id")
        return {"result": State.Authorization.READY, "client": client}


def error_event_handle(
    client: ClientModel, event: Dict[str, Any]
) -> Optional[dict]:
    logging.warning(f"Got error {event=} for {client.phone=}")
    client_id = client.client_id
    error_message = event.get("message")
    if error_message == TypeMessage.Error.PHONE_CODE_INVALID:
        code = input("Неверный код. Введите код повторно: ")
        telegram_json.send_code(client_id, code)
    elif error_message == TypeMessage.Error.PASSWORD_HASH_INVALID:
        password = input("Неверный пароль. Введите пароль повторно: ")
        telegram_json.send_password(client_id, password)
    elif error_message == TypeMessage.Error.PHONE_CODE_EXPIRED:
        return {
            "result": TypeMessage.Error.PHONE_CODE_EXPIRED,
            "client": client,
        }
    elif TypeMessage.Error.LOCK_FILE in error_message:
        return TypeMessage.Error.LOCK_FILE
    else:
        logging.warning(f"Unhandled error: {error_message}")


def update_new_messages_handle(
    client: ClientModel, event: Dict[str, Any]
) -> None:
    message_id = event.get("message").get("id")
    chat_id = event.get("message").get("chat_id")
    text = event.get("message").get("content").get("text")
    caption = event.get("message").get("content").get("caption")
    text = caption if not text else text

    is_channel_post = event.get("message").get("is_channel_post")

    sender_user_id = event.get("message").get("sender_id").get("user_id")

    logging.debug(
        (
            f"Got text message for {client.phone}:"
            f" {chat_id}_{sender_user_id}; {text=}"
        )
    )

    if not (
        text
        and not is_channel_post
        and sender_user_id != client.telegram_user_id
    ):
        return

    text = text.get("text")

    with session_maker() as session:
        account = get_account_data(session, client.telegram_user_id)

        answer = None

        is_group_chat = chat_id != sender_user_id

        if is_group_chat:
            answer = create_group_message(account, sender_user_id, text)

        else:
            answer = create_private_message(account, sender_user_id, text)

        if answer:
            reply_to_message_id = message_id if is_group_chat else 0  # 0 -
            # without reply mark

            telegram_json.send_text_message(
                client_id=client.client_id,
                chat_id=chat_id,
                text=answer,
                reply_to_message_id=reply_to_message_id,
            )
