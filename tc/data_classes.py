from dataclasses import dataclass
from typing import Optional


@dataclass
class ClientModel:
    client_id: int

    phone: str
    api_id: int
    api_hash: str
    account_id: Optional[int] = None
    telegram_user_id: Optional[int] = None


class TypeMessage:
    class Error:
        PHONE_CODE_INVALID = "PHONE_CODE_INVALID"
        PASSWORD_HASH_INVALID = "PASSWORD_HASH_INVALID"
        PHONE_CODE_EXPIRED = "PHONE_CODE_EXPIRED"

        LOCK_FILE = "Can't lock file"


class State:
    class Authorization:
        READY = "authorization ready"
