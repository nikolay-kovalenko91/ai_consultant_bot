import os
import shutil
from dataclasses import dataclass
from threading import Thread

from database import TelegramClientAccount
from tc.tc_constants import TC_SESSIONS_DIRECTORY, EventTypes
from tc.tc_event_handlers import authorization_event_handle, \
    error_event_handle, update_new_messages_handle, \
    user_event_handle
from tc.tc_listener import listen_client
from tc.tc_telegram_json import TelegramJSON

telegram_json = TelegramJSON()
telegram_json.add_event_handler(EventTypes.ERROR, error_event_handle)
telegram_json.add_event_handler(EventTypes.UPDATE_AUTHORIZATION_STATE,
                                authorization_event_handle)
telegram_json.add_event_handler(EventTypes.USER, user_event_handle)
telegram_json.add_event_handler(EventTypes.UPDATE_NEW_MESSAGE,
                                update_new_messages_handle)


@dataclass
class TelegramClient:
    telegram_account: TelegramClientAccount

    def init(self, only_registration=False):

        client = telegram_json.client_create(
            self.telegram_account.phone,
            self.telegram_account.api_id,
            self.telegram_account.api_hash
        )
        client.telegram_user_id = self.telegram_account.telegram_user_id

        telegram_json.get_authorization_state(client.client_id)

        if only_registration:

            session_path = f"{TC_SESSIONS_DIRECTORY}" \
                           f"/{self.telegram_account.phone}"
            if not os.path.exists(session_path):
                os.makedirs(session_path)
                shutil.copy("tc/libs/td.binlog", f"{session_path}/td.binlog")

            listen_client(client, only_registration)

        else:
            params = {'client': client, 'only_registration': only_registration}
            thread = Thread(target=listen_client, kwargs=params)
            thread.start()
