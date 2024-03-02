from sqlalchemy import select

from database import AvitoAccounts, session_maker, Faq


def get_active_avito_accounts() -> list[AvitoAccounts]:
    with session_maker() as session:
        statement = select(AvitoAccounts).filter_by(is_active=True)
        active_accounts = session.scalars(statement).all()

        return active_accounts


def get_avito_accounts_faqs(user_id: int) -> tuple[str, str]:
    with session_maker() as session:
        statement = select(Faq.question, Faq.answer).filter_by(account_id=user_id)
        faqs = session.execute(statement).all()

        return faqs
