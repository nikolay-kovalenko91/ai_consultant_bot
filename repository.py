from sqlalchemy import select, update

from database import Accounts, session_maker


def get_active_accounts() -> list[Accounts]:
    with session_maker() as session:
        statement = select(Accounts).filter_by(is_active=True)
        active_accounts = session.scalars(statement).all()
        return active_accounts
