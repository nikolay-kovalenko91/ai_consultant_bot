from dataclasses import dataclass


@dataclass
class ClientModel:
    client_id: int

    phone: str
    account_id: int = -1
    api_id: int = None
    api_hash: str = None
    telegram_user_id: int = None
