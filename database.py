from sqlalchemy import create_engine
from sqlalchemy.orm import Mapped, sessionmaker, declarative_base, mapped_column

engine = create_engine('sqlite:///database.db')
session_maker = sessionmaker(
    engine, expire_on_commit=False,
)

Base = declarative_base()


class Accounts(Base):
    __tablename__ = 'accounts'

    user_id: Mapped[str] = mapped_column(primary_key=True)
    client_id: Mapped[str]
    client_secret: Mapped[str]
    is_active: Mapped[bool]
    prompt: Mapped[str]


class Faq(Base):
    __tablename__ = 'faq'

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str]
    answer: Mapped[str]


Base.metadata.create_all(engine)
