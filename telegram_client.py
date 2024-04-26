import logging
import os
import time

from constants import BASE_FOLDER
from database import session_maker
from tc.tc_repository import get_telegram_accounts
from tc.tc_constants import TC_SESSIONS_DIRECTORY, POLLING_INTERVAL, DATABASE_DIRECTORY, TCEngine
from tc.tc_telegram_client import TelegramClient

logging.basicConfig(
    level=logging.INFO,
    format='[{asctime}] #{levelname:8} {filename}:'
           '{lineno} - {name} - {message}',
    style='{'
)


accounts = []

if __name__ == '__main__':

    if not os.path.exists(DATABASE_DIRECTORY):
        os.makedirs(DATABASE_DIRECTORY)

    if not os.path.exists(TC_SESSIONS_DIRECTORY):
        os.makedirs(TC_SESSIONS_DIRECTORY)

    if not os.path.exists(f"{BASE_FOLDER}/{TCEngine.PRIVATE_MESSAGE}"):
        os.makedirs(f"{BASE_FOLDER}/{TCEngine.PRIVATE_MESSAGE}")

    if not os.path.exists(f"{BASE_FOLDER}/{TCEngine.GROUP_MESSAGE}"):
        os.makedirs(f"{BASE_FOLDER}/{TCEngine.GROUP_MESSAGE}")

    while True:
        with session_maker() as session:
            telegram_accounts = get_telegram_accounts(session)

            for account in telegram_accounts:
                if not any(phone == account.phone for phone in accounts):
                    if os.path.exists(f"{TC_SESSIONS_DIRECTORY}/{account.phone}"):
                        accounts.append(account.phone)
                        telegram_client = TelegramClient(account)
                        telegram_client.init()

        time.sleep(POLLING_INTERVAL)
