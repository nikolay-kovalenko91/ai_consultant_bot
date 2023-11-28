import os

# Config
POLLING_INTERVAL = int(os.environ.get("POLLING_INTERVAL", 10))

# Avito
AVITO_USER_ID = os.environ["AVITO_USER_ID"]
CLIENT_ID = os.environ["AVITO_CLIENT_ID"]
CLIENT_SECRET = os.environ["AVITO_CLIENT_SECRET"]

# Telegram
TELEGRAM_BOT_TOKEN = os.environ["BOT_TOKEN"]

# OpenAI
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SYSTEM_PROMPT = os.environ["SYSTEM_PROMPT"]

# Email credentials
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = os.environ.get("SMTP_SERVER_PORT", 587)
SMTP_EMAIL = os.environ["SENDER_EMAIL_ADDRESS"]
SMTP_PASSWORD = os.environ["SENDER_EMAIL_PASS"]

# Folder names
BASE_FOLDER = "history"
SUB_FOLDER = "avito"

# Email message const
EMAIL_RECEIVER = os.environ["RECEIVER_EMAIL_ADDRESS"]
CLOSING_MESSAGE_SUBJECT = "Номер кандидата"
CLOSING_MESSAGE_BODY = "Контактный номер кандидата:"

CLOSING_MESSAGE = "Спасибо, в рабочее время мы с вами свяжемся!"
