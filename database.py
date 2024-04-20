from sqlalchemy.orm import (
    Mapped,
    sessionmaker,
    declarative_base,
    mapped_column,
    relationship,
    scoped_session,
)
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from typing import Optional
from constants import DATABASE_DNS

engine = create_engine(DATABASE_DNS)
session_maker = sessionmaker(
    engine,
    expire_on_commit=False,
)
current_session = scoped_session(session_maker)
Base = declarative_base()


class AvitoAccounts(Base):
    __tablename__ = "avito_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[Optional[str]]
    client_id: Mapped[str]
    client_secret: Mapped[str]
    is_active: Mapped[bool]
    prompt_id = Column(Integer, ForeignKey("prompts.id"))

    prompt = relationship("Prompt", back_populates="avito_accounts")
    faqs: Mapped[list["Faq"]] = relationship(
        back_populates="account",
    )


class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"

    id = Column(Integer, primary_key=True)
    token = Column(String)
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    is_active: Mapped[bool]

    prompt = relationship("Prompt", back_populates="telegram_accounts")


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True)
    text = Column(String)

    telegram_accounts = relationship(
        "TelegramAccount", back_populates="prompt"
    )
    avito_accounts = relationship("AvitoAccounts", back_populates="prompt")


class Faq(Base):
    __tablename__ = "faq"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("avito_accounts.id"),
    )
    question: Mapped[str]
    answer: Mapped[str]

    account: Mapped["AvitoAccounts"] = relationship(back_populates="faqs")


Base.metadata.create_all(engine)
