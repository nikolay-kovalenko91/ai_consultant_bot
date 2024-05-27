import logging

from database import TelegramClientAccount
from tc.telegram_client import TelegramClient


logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] #{levelname:8} {filename}:"
    "{lineno} - {name} - {message}",
    style="{",
)

if __name__ == "__main__":
    while True:
        phone = input("Введите номер телефона: ")
        api_id = input("Введите api_id: ")
        api_hash = input("Введите api_hash: ")

        account = TelegramClientAccount()
        account.phone = phone
        account.api_id = api_id
        account.api_hash = api_hash

        telegram_client = TelegramClient(account)
        listener = telegram_client.init(only_registration=True)

        while True:
            if next(listener):
                break
