from typing import Optional

from sqlalchemy import create_engine, ForeignKey, Column, Integer, String
from sqlalchemy.orm import (
    Mapped,
    sessionmaker,
    declarative_base,
    mapped_column,
    relationship,
    scoped_session,
)

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
    prompt: Mapped[str]

    faqs: Mapped[list["Faq"]] = relationship(
        back_populates="account",
    )


class Faq(Base):
    __tablename__ = "faq"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("avito_accounts.id"),
    )
    question: Mapped[str]
    answer: Mapped[str]

    account: Mapped["AvitoAccounts"] = relationship(back_populates="faqs")


class TelegramClientAccount(Base):
    __tablename__ = "telegram_client_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    is_active: Mapped[bool]

    telegram_user_id: Mapped[int]
    phone: Mapped[str]
    api_id: Mapped[int]
    api_hash: Mapped[str]

    private_message_prompt_id = Column(Integer, ForeignKey("prompts.id"))
    group_message_prompt_id = Column(Integer, ForeignKey("prompts.id"))

    private_message_prompt = relationship(
        "Prompt",
        foreign_keys=[private_message_prompt_id],
        back_populates="telegram_client_accounts_private")

    group_message_prompt = relationship(
        "Prompt",
        foreign_keys=[group_message_prompt_id],
        back_populates="telegram_client_accounts_group")

    keywords: Mapped[Optional[str]]


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    text = Column(String)

    telegram_client_accounts_private = relationship(
        "TelegramClientAccount",
        foreign_keys=[TelegramClientAccount.private_message_prompt_id],
        back_populates="private_message_prompt"
    )

    telegram_client_accounts_group = relationship(
        "TelegramClientAccount",
        foreign_keys=[TelegramClientAccount.group_message_prompt_id],
        back_populates="group_message_prompt"
    )


Base.metadata.create_all(engine)
