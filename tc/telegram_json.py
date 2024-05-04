import json
import os
import platform
from ctypes import c_char_p, CDLL, c_void_p, c_double
from typing import List, Optional, Callable, Dict, Any, Union

from tc.client_model import ClientModel


class TelegramJSON:
    singleton = None

    _td_json_client_create = None
    _td_json_client_destroy = None
    _td_json_client_send = None
    _td_json_client_receive = None
    _td_json_client_execute = None

    clients: List[ClientModel] = []
    event_handlers = {}

    def __new__(cls, *args, **kwargs):
        if cls.singleton is None:
            path = os.path.dirname(os.path.realpath(__file__))

            os_name = platform.system()
            dll = None
            if os_name == "Windows":
                dll = os.path.join(path, "libs/tdjson.dll")
            elif os_name == "Linux":
                dll = os.path.join(path, "libs/libtdjson.so.1.8.28")
            tdjson = CDLL(dll)

            cls._td_json_client_create = tdjson.td_json_client_create
            cls._td_json_client_create.restype = c_void_p
            cls._td_json_client_create.argtypes = []

            cls._td_json_client_destroy = tdjson.td_json_client_destroy
            cls._td_json_client_destroy.restype = None
            cls._td_json_client_destroy.argtypes = [c_void_p]

            cls._td_json_client_send = tdjson.td_json_client_send
            cls._td_json_client_send.restype = None
            cls._td_json_client_send.argtypes = [c_void_p, c_char_p]

            cls._td_json_client_receive = tdjson.td_json_client_receive
            cls._td_json_client_receive.restype = c_char_p
            cls._td_json_client_receive.argtypes = [c_void_p, c_double]

            cls._td_json_client_execute = tdjson.td_json_client_execute
            cls._td_json_client_execute.restype = None
            cls._td_json_client_execute.argtypes = [c_void_p, c_char_p]

            cls.singleton = object.__new__(cls)

        return cls.singleton

    @classmethod
    def add_event_handler(cls, event_type: str, handler: Callable) -> None:
        cls.event_handlers[event_type] = handler

    @classmethod
    def call_event_handle(
        cls, client: ClientModel, event_type: str, event: Dict[str, Any]
    ) -> Optional[dict]:
        handle = cls.event_handlers.get(event_type)
        return handle(client, event) if handle else None

    @classmethod
    def client_create(
        cls, phone: str, api_id: int, api_hash: str
    ) -> ClientModel:
        client_id = cls._td_json_client_create()
        client = ClientModel(
            client_id=client_id, phone=phone, api_id=api_id, api_hash=api_hash
        )
        cls.clients.append(client)
        return client

    @classmethod
    def get_authorization_state(cls, client_id: int) -> None:
        cls.td_json_client_execute(
            client_id,
            {
                "@type": "setLogVerbosityLevel",
                "new_verbosity_level": 1,
            },
        )
        cls.td_json_client_send(
            client_id, {"@type": "getAuthorizationState", "@extra": 1.01234}
        )

    @classmethod
    def client_destroy(cls, client_id: int) -> None:
        cls._td_json_client_destroy(client_id)

    @classmethod
    def td_json_client_execute(
        cls, client_id: int, query: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        query = json.dumps(query).encode("utf-8")
        result = cls._td_json_client_execute(client_id, query)
        if result:
            result = json.loads(result.decode("utf-8"))
        return result

    @classmethod
    def td_json_client_send(
        cls, client_id: int, query: Dict[str, Any]
    ) -> None:
        query = json.dumps(query).encode("utf-8")
        cls._td_json_client_send(client_id, query)

    @classmethod
    def td_json_client_receive(cls, client_id: int) -> Optional[dict]:
        result = cls._td_json_client_receive(client_id, 1.0)
        if result:
            result = json.loads(result.decode("utf-8"))
        return result

    @classmethod
    def send_parameters(
        cls, client_id: int, db_path: str, api_id: int, api_hash: str
    ) -> None:
        parameters = {
            "database_directory": db_path,
            "use_chat_info_database": True,
            "use_message_database": True,
            "use_secret_chats": True,
            "api_id": api_id,
            "api_hash": api_hash,
            "system_language_code": "en",
            "device_model": "Desktop",
            "application_version": "1.0",
            "enable_storage_optimizer": False,
            "ignore_file_names": False,
        }
        cls.td_json_client_send(
            client_id,
            {
                "@type": "setTdlibParameters",
                "parameters": parameters,
                **parameters,
            },
        )

    @classmethod
    def check_database_encryption_key(cls, client_id: int) -> None:
        cls.td_json_client_send(
            client_id,
            {"@type": "checkDatabaseEncryptionKey", "encryption_key": ""},
        )

    @classmethod
    def send_phone(cls, client_id: int, phone: str) -> None:
        cls.td_json_client_send(
            client_id,
            {"@type": "setAuthenticationPhoneNumber", "phone_number": phone},
        )

    @classmethod
    def send_code(cls, client_id: int, code: str) -> None:
        cls.td_json_client_send(
            client_id, {"@type": "checkAuthenticationCode", "code": code}
        )

    @classmethod
    def send_password(cls, client_id: int, password: str) -> None:
        cls.td_json_client_send(
            client_id,
            {"@type": "checkAuthenticationPassword", "password": password},
        )

    @classmethod
    def get_me(cls, client_id: int) -> None:
        cls.td_json_client_send(
            client_id,
            {
                "@type": "getMe",
                "@extra": {"type": "getMe", "client_id": client_id},
            },
        )

    @classmethod
    def send_text_message(
        cls,
        client_id: int,
        chat_id: int,
        text: str,
        reply_to_message_id: int = 0,
        extra: Union[int, str, dict, None] = None,
    ) -> None:
        text_format = {"@type": "formattedText", "text": text, "entities": []}

        input_message_text = {
            "@type": "inputMessageText",
            "text": text_format,
            "disable_web_page_preview": False,
            "clear_draft": True,
        }

        reply_to = None
        if reply_to_message_id:
            reply_to = {
                "@type": "inputMessageReplyToMessage",
                "chat_id": chat_id,
                "message_id": reply_to_message_id,
            }

        cls.td_json_client_send(
            client_id,
            {
                "@type": "sendMessage",
                "chat_id": chat_id,
                "reply_to_message_id": reply_to_message_id,
                "reply_to": reply_to,
                "input_message_content": input_message_text,
                "@extra": extra,
            },
        )
