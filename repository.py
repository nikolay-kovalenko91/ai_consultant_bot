from typing import Sequence

from sqlalchemy import select, Row
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from database import AvitoAccounts, Faq, TelegramAccount


def get_active_avito_accounts(session: Session) -> Sequence[AvitoAccounts]:
    return (
        session.query(AvitoAccounts)
        .options(joinedload(AvitoAccounts.prompt))
        .filter_by(is_active=True)
    )


def get_active_telegram_bot_accounts(
    session: Session,
) -> Sequence[TelegramAccount]:
    return (
        session.query(TelegramAccount)
        .options(joinedload(TelegramAccount.prompt))
        .filter_by(is_active=True)
    )


def get_avito_accounts_faqs(
    session: Session,
    account_id: int,
) -> Sequence[Row[tuple[str, str]]]:
    statement = select(Faq.question, Faq.answer).filter_by(
        account_id=account_id,
    )

    return session.execute(statement).all()
