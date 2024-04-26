from sqlalchemy.orm import Session

from typing import Sequence
from tc.tc_client_model import ClientModel

from database import TelegramClientAccount, Prompt


def get_telegram_accounts(session: Session) -> Sequence[TelegramClientAccount]:
    return session.query(TelegramClientAccount).all()


def add_telegram_account(session: Session, client: ClientModel):
    if not session.query(TelegramClientAccount).filter_by(phone=client.phone).first():
        account = TelegramClientAccount(
            telegram_user_id=client.telegram_user_id,
            phone=client.phone,
            api_id=client.api_id,
            api_hash=client.api_hash,
            is_active=True,
        )
        session.add(account)
        session.commit()


def get_prompt_data(session: Session, prompt_id: int):
    if not prompt_id:
        return

    prompt = session.query(Prompt).filter(
        Prompt.id == prompt_id
    ).first()

    return prompt.text if prompt else None


def get_account_data(session: Session, telegram_user_id: int):
    account: TelegramClientAccount = session.query(TelegramClientAccount).filter(
        TelegramClientAccount.telegram_user_id == telegram_user_id
    ).first()

    return account
