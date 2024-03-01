from sqlalchemy import select

from database import AvitoAccounts, session_maker, Faq


def get_active_avito_accounts() -> list[AvitoAccounts]:
    with session_maker() as session:
        statement = select(AvitoAccounts).filter_by(is_active=True)
        active_accounts = session.scalars(statement).all()

        return active_accounts


def get_avito_account_prompt(user_id):
    with session_maker() as session:
        statement = select(AvitoAccounts.prompt).filter_by(user_id=user_id)
        account_prompt = session.scalars(statement).first()

        return account_prompt


def get_avito_accounts_faqs(user_id):
    with session_maker() as session:
        statement = select(Faq.question, Faq.answer).filter_by(account_id=user_id)
        faqs = session.execute(statement).all()

        return faqs

