<h2>ChatGPT Bots for Telegram and Avito </h2>

This repository implements two bots for Telegram and Avito using ChatGPT. The Telegram bot supports commands such as `/start` and `/reset` to interact with users.


<br>

## Telegram Bot Commands
`/start` - Starts new conversation with users
`/reset` - Cleans user conversation from history

<br>

## Running the Bots Locally with Python Scripts

Before running the bots, ensure you have the required packages installed. Follow these steps:

## Install Requirements

- Navigate to the bot directory.
- (Optional) Create a virtual environment if needed.
- Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

<br>

## Environment Setup
Ensure you have the following environment variables set up:


```
OPENAI_API_KEY: ChatGPT API key

DATABASE_DNS: Database connection string. You can omit it and then it will be 
selected by default. If the custom path is still specified, 
then you need to redefine the mount folders in docker-compose.yml 

SMTP_SERVER: SMTP server address
SMTP_SERVER_PORT: SMTP server port
SENDER_EMAIL_ADDRESS: Sending account address
SENDER_EMAIL_PASS: Sending account password

RECEIVER_EMAIL_ADDRESS: Email address of reciever 
```
<br>

## Running the Bots

If you run the bot from the command line, ensure the database directory exists

## Telegram Bot

To launch the Telegram bot, run:

```bash
python telegram_bot.py
```

## Avito Bot

To launch the Telegram bot, run:

```bash
python avito_bot.py
```

To see logs without sending actual API calls, run the Avito bot in dry mode:

```bash
python avito_bot.py --dry
```

## Telegram clients

To launch the Telegram clients, run:

```bash
python telegram_client.py
```

## Authorization of Telegram clients

For registering accounts:
<br>
- Enter the command:
```bash
python telegram_client_authorization.py
```
- Enter the phone number (+79101234567)
- Enter api_id
- Enter api_hash
- Enter the security code
- Enter the password (if two-factor authentication is installed)
<br>After a few seconds, an account entry will appear in the database.
- Set up prompts in the database

## Running the Bots with Docker

To launch the Telegram and Avito bots together with docker, use:

```bash
docker compose -f docker-compose up --build
```

Nocodb will be available on localhost:8080. 
In it you need to add a new Data Source with 
the 'SQLite' Database Type and '/usr/src/app/database/< database file name >' SQLite File.