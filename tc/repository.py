import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from typing import Sequence

from database import TelegramClientAccount
from tc.data_classes import ClientModel


def get_telegram_accounts(session: Session) -> Sequence[TelegramClientAccount]:
    return session.query(TelegramClientAccount).all()


def add_telegram_account(session: Session, client: ClientModel) -> None:
    try:
        account = TelegramClientAccount(
            telegram_user_id=client.telegram_user_id,
            phone=client.phone,
            api_id=client.api_id,
            api_hash=client.api_hash,
            is_active=True,
        )
        session.add(account)
        session.commit()

    except IntegrityError:
        logging.error(f"Account has been already saved: {client.phone}")


def get_account_data(
    session: Session, telegram_user_id: int
) -> TelegramClientAccount:
    account: TelegramClientAccount = (
        session.query(TelegramClientAccount)
        .options(joinedload(TelegramClientAccount.group_message_prompt))
        .options(joinedload(TelegramClientAccount.private_message_prompt))
        .filter(TelegramClientAccount.telegram_user_id == telegram_user_id)
        .first()
    )

    return account
