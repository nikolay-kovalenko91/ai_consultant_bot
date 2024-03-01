import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import StringIO

from constants import (
    SMTP_EMAIL,
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_PASSWORD,
    EMAIL_RECEIVER,
    CLOSING_MESSAGE_SUBJECT,
    CLOSING_MESSAGE_BODY,
)
from repository import get_avito_account_prompt, get_avito_accounts_faqs


def send_email(to_address: str, subject: str, body: str) -> None:
    """
    Function to send email message
    """

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Connect to SMTP and send email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_address, msg.as_string())


def send_contact(phone: str) -> None:
    """
    Function to send contact number
    """
    send_email(
        EMAIL_RECEIVER,
        CLOSING_MESSAGE_SUBJECT,
        f"{CLOSING_MESSAGE_BODY} {phone}",
    )


def to_csv_string(sql_rows: list[tuple]) -> str:
    csv_result = StringIO()
    wr = csv.writer(csv_result)
    for sql_row in sql_rows:
        wr.writerow(sql_row)

    return csv_result.getvalue()


def generate_gpt_prompt(user_id: str) -> str:
    account_prompt = get_avito_account_prompt(user_id)
    accounts_faqs = to_csv_string(get_avito_accounts_faqs(user_id))

    return f'{account_prompt}\n{accounts_faqs}'
