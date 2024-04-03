from typing import Sequence

from sqlalchemy import select, Row
from sqlalchemy.orm import Session

from database import AvitoAccounts, Faq


def get_active_avito_accounts(session: Session) -> Sequence[AvitoAccounts]:
    statement = select(AvitoAccounts).filter_by(is_active=True)

    return session.scalars(statement).all()


def get_avito_accounts_faqs(
    session: Session,
    account_id: int,
) -> Sequence[Row[tuple[str, str]]]:
    statement = select(Faq.question, Faq.answer).filter_by(account_id=account_id)

    return session.execute(statement).all()
