
POLLING_INTERVAL = 10

DATABASE_DIRECTORY = "database"

DATABASE_DNS = "sqlite:///database/database.db"

TC_SESSIONS_DIRECTORY = 'telegram_client_sessions'


class TCEngine:
    GROUP_MESSAGE = 'tg_client_group_messages'
    PRIVATE_MESSAGE = 'tg_client_private_messages'


class EventTypes:
    ERROR = 'error'
    USER = 'user'
    UPDATE_AUTHORIZATION_STATE = "updateAuthorizationState"
    UPDATE_NEW_MESSAGE = "updateNewMessage"
    MESSAGE = "message"


class TypeMessage:
    class Error:
        PHONE_CODE_INVALID = 'PHONE_CODE_INVALID'
        PASSWORD_HASH_INVALID = 'PASSWORD_HASH_INVALID'
        PHONE_CODE_EXPIRED = 'PHONE_CODE_EXPIRED'

        LOCK_FILE = 'Can\'t lock file'


class State:
    class Authorization:
        READY = "authorization ready"