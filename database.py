from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import Mapped, sessionmaker, declarative_base, mapped_column, relationship

engine = create_engine('sqlite:///database.db')
session_maker = sessionmaker(
    engine, expire_on_commit=False,
)

Base = declarative_base()


class AvitoAccounts(Base):
    __tablename__ = 'avito_accounts'

    user_id: Mapped[str] = mapped_column(primary_key=True)
    client_id: Mapped[str]
    client_secret: Mapped[str]
    is_active: Mapped[bool]
    prompt: Mapped[str]

    faqs: Mapped[list['Faq']] = relationship(back_populates='account')


class Faq(Base):
    __tablename__ = 'faq'

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey('avito_accounts.user_id'))
    question: Mapped[str]
    answer: Mapped[str]

    account: Mapped['AvitoAccounts'] = relationship(back_populates='faqs')


Base.metadata.create_all(engine)
