import logging
import os
import time
from threading import Thread

from constants import (
    BASE_FOLDER,
    POLLING_INTERVAL,
    TC_SESSIONS_DIRECTORY,
    TCEngine,
)
from database import session_maker
from tc.repository import get_telegram_accounts
from tc.telegram_client import TelegramClient

logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] #{levelname:8} {filename}:"
    "{lineno} - {name} - {message}",
    style="{",
)


accounts = []


def run_account_listeners():
    while True:
        for a in accounts:
            e_client = a.get("events_client")
            if e_client:
                next(e_client)


if __name__ == "__main__":
    if not os.path.exists(TC_SESSIONS_DIRECTORY):
        os.makedirs(TC_SESSIONS_DIRECTORY)

    if not os.path.exists(f"{BASE_FOLDER}/{TCEngine.PRIVATE_MESSAGE}"):
        os.makedirs(f"{BASE_FOLDER}/{TCEngine.PRIVATE_MESSAGE}")

    if not os.path.exists(f"{BASE_FOLDER}/{TCEngine.GROUP_MESSAGE}"):
        os.makedirs(f"{BASE_FOLDER}/{TCEngine.GROUP_MESSAGE}")

    Thread(target=run_account_listeners).start()

    while True:
        with session_maker() as session:
            telegram_accounts = get_telegram_accounts(session)

            for account in telegram_accounts:
                if not any(a.get("phone") == account.phone for a in accounts):
                    if os.path.exists(
                        f"{TC_SESSIONS_DIRECTORY}/{account.phone}"
                    ):
                        telegram_client = TelegramClient(account)
                        events_client = telegram_client.init()
                        accounts.append(
                            {
                                "phone": account.phone,
                                "events_client": events_client
                            }
                        )
                        logging.info(
                            f"Start listening account:"
                            f" {account.phone}/{account.name}"
                        )

                    else:
                        logging.warning(
                            f"Account not added, it needs to be registered"
                            f" first: {account.phone}/{account.name}"
                        )

        time.sleep(POLLING_INTERVAL)
