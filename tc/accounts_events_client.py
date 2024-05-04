from typing import Generator

from database import session_maker
from tc.client_model import ClientModel, State, TypeMessage
from tc.repository import add_telegram_account
from tc.telegram_json import TelegramJSON

import time

telegram_json = TelegramJSON()
DELAY = 5


def accounts_events_client(
    client: ClientModel, only_registration: bool = False
) -> Generator:
    time.sleep(DELAY)
    while True:
        event = telegram_json.td_json_client_receive(client.client_id)

        if event:
            result = telegram_json.call_event_handle(
                client, event["@type"], event
            )

            if only_registration and result:
                if result.get("result") == State.Authorization.READY:
                    telegram_json.client_destroy(client.client_id)
                    time.sleep(DELAY)
                    with session_maker() as session:
                        add_telegram_account(session, result.get("client"))

                    yield True

                elif (
                    result.get("result")
                    == TypeMessage.Error.PHONE_CODE_EXPIRED
                ):
                    telegram_json.client_destroy(client.client_id)
                    time.sleep(DELAY)

                    yield True

        yield
