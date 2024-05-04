import os
import shutil
from dataclasses import dataclass
from typing import Generator

from constants import TC_SESSIONS_DIRECTORY
from database import TelegramClientAccount
from tc.event_handlers import (
    authorization_event_handle,
    error_event_handle,
    update_new_messages_handle,
    user_event_handle,
)
from tc.accounts_events_client import accounts_events_client
from tc.telegram_json import TelegramJSON


class EventTypes:
    ERROR = "error"
    USER = "user"
    UPDATE_AUTHORIZATION_STATE = "updateAuthorizationState"
    UPDATE_NEW_MESSAGE = "updateNewMessage"
    MESSAGE = "message"


telegram_json = TelegramJSON()
telegram_json.add_event_handler(EventTypes.ERROR, error_event_handle)
telegram_json.add_event_handler(
    EventTypes.UPDATE_AUTHORIZATION_STATE, authorization_event_handle
)
telegram_json.add_event_handler(EventTypes.USER, user_event_handle)
telegram_json.add_event_handler(
    EventTypes.UPDATE_NEW_MESSAGE, update_new_messages_handle
)


@dataclass
class TelegramClient:
    telegram_account: TelegramClientAccount

    def init(self, only_registration: bool = False) -> Generator:
        client = telegram_json.client_create(
            self.telegram_account.phone,
            self.telegram_account.api_id,
            self.telegram_account.api_hash,
        )
        client.telegram_user_id = self.telegram_account.telegram_user_id

        telegram_json.get_authorization_state(client.client_id)

        if only_registration:
            session_path = (
                f"{TC_SESSIONS_DIRECTORY}/{self.telegram_account.phone}"
            )
            if not os.path.exists(session_path):
                os.makedirs(session_path)
                shutil.copy("tc/libs/td.binlog", f"{session_path}/td.binlog")

        return accounts_events_client(client, only_registration)
