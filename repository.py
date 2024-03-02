from sqlalchemy import select

from database import AvitoAccounts, Faq, current_session


def get_active_avito_accounts() -> list[AvitoAccounts]:
    statement = select(AvitoAccounts).filter_by(is_active=True)
    active_accounts = current_session.scalars(statement).all()

    return active_accounts


def get_avito_accounts_faqs(user_id: int) -> list[tuple[str, str]]:
    statement = select(Faq.question, Faq.answer).filter_by(account_id=user_id)
    faqs = current_session.execute(statement).all()

    return faqs
