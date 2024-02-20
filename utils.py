import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from constants import (
    SMTP_EMAIL,
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_PASSWORD,
    EMAIL_RECEIVER,
    CLOSING_MESSAGE_SUBJECT,
    CLOSING_MESSAGE_BODY,
)


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
