import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Config
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
POLLING_INTERVAL = int(os.environ.get("POLLING_INTERVAL", 10))
BREAK_TIME = int(os.environ.get("BREAK_TIME", 3))

# Avito
DATABASE_DNS = os.environ.get("DATABASE_DNS", "sqlite:///database/database.db")

# OpenAI
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SYSTEM_PROMPT = os.environ["SYSTEM_PROMPT"]
GPT_ERROR_CASE_MESSAGE = "Мы ответим вам как можно скорее"

# Email credentials
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = os.environ.get("SMTP_SERVER_PORT", 587)
SMTP_EMAIL = os.environ["SENDER_EMAIL_ADDRESS"]
SMTP_PASSWORD = os.environ["SENDER_EMAIL_PASS"]

# Folder names
BASE_FOLDER = "history"
SUB_FOLDER_AVITO = "avito"
SUB_FOLDER_TG = "telegram"
TC_SESSIONS_DIRECTORY = "telegram_client_sessions"


class TCEngine:
    GROUP_MESSAGE = "tg_client_group_messages"
    PRIVATE_MESSAGE = "tg_client_private_messages"


# Email message const
EMAIL_RECEIVER = os.environ["RECEIVER_EMAIL_ADDRESS"]
CLOSING_MESSAGE_SUBJECT = "Номер кандидата"
CLOSING_MESSAGE_BODY = "Контактный номер кандидата:"

CLOSING_MESSAGE = "Спасибо, в рабочее время мы с вами свяжемся!"

NON_TEXT_EMAIL_MESSAGE_SUBJECT = "Не текстовое сообщение"
NON_TEXT_EMAIL_MESSAGE_BODY = (
    "Пользователь прислал не текстовое сообщение в ответ на сообщение:"
)
