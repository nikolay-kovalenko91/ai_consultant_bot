import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


def send_email(to_address: str, subject: str, body: str) -> None:
    """
    Function to send email message
    """

    # Set up credentials
    smtp_server = os.environ.get(
        "SMTP_SERVER", "smtp.gmail.com"
    )  # Assume we are using GMAIL
    smtp_port = os.environ.get("SMTP_SERVER_PORT", 587)
    smtp_username = os.environ["SENDER_EMAIL_ADDRESS"]
    smtp_password = os.environ["SENDER_EMAIL_PASS"]

    msg = MIMEMultipart()
    msg["From"] = smtp_username
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Connect to SMTP and send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_address, msg.as_string())


def send_token_error(status_code: str, response: str) -> None:
    """
    Function to send token error email
    """

    receiver = os.environ["RECEIVER_EMAIL_ADDRESS"]
    subject = "Failed to get access token"

    # Can be reformed using HTML template
    body = (
        f"Failed to get access token. "
        f"Status code: {status_code}, Response: {response}"
    )

    send_email(receiver, subject, body)


def send_contact(phone: str) -> None:
    """
    Function to send contact number
    """

    receiver = os.environ["RECEIVER_EMAIL_ADDRESS"]
    subject = "Номер кандидата"

    # Can be reformed using HTML template
    body = f"Контактный номер кандидата: {phone}"

    send_email(receiver, subject, body)
