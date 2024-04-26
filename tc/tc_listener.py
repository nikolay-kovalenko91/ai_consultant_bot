from database import session_maker
from tc.tc_client_model import ClientModel
from tc.tc_constants import State, TypeMessage
from tc.tc_repository import add_telegram_account
from tc.tc_telegram_json import TelegramJSON

import time

telegram_json = TelegramJSON()
DELAY = 5


def listen_client(client: ClientModel, only_registration: bool = False):
    time.sleep(DELAY)
    while True:

        event = telegram_json.td_json_client_receive(client.client_id)

        if event:

            result = telegram_json.call_event_handle(
                client,
                event['@type'],
                event
            )

            if only_registration and result:
                if result.get('result') == State.Authorization.READY:
                    telegram_json.client_destroy(client.client_id)
                    time.sleep(DELAY)
                    with session_maker() as session:
                        add_telegram_account(session, result.get('client'))
                    break
                elif result.get('result') ==\
                        TypeMessage.Error.PHONE_CODE_EXPIRED:
                    telegram_json.client_destroy(client.client_id)
                    time.sleep(DELAY)
                    break
