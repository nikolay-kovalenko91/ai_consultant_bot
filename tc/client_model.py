from dataclasses import dataclass
from typing import Optional


@dataclass
class ClientModel:
    client_id: int

    phone: str
    account_id: Optional[int] = None
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    telegram_user_id: Optional[int] = None
