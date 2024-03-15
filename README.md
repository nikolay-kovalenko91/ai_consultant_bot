
<h2>ChatGPT Bot for Telegram and Avito  </h2>

This repository implements two bots for Telegram and Avito using ChatGPT. Users can run the `telegram_bot.py` for Telegram and `avito_bot.py` for Avito. The Telegram bot supports commands such as viewing chat history and resetting it.


<br>

# ▋Telegram Bot Commands
+ **/history** to get history file in json format
+ **/reset** to reset the chat history

<br>

# ▋Install Requirements
Before running the bots, install the required packages. Navigate to the bot directory, create a virtual environment if needed, and install dependencies:
1. Navigate to bot directory
2. Create virtual environment if needed
3. Install requirements using pip
```bash
pip install -r requirements.txt
```

<br>

# ▋Setup envs
```
BOT_TOKEN: Telegram API key
OPENAI_API_KEY: ChatGPT API key
SYSTEM_PROMPT: ChatGPT system prompt

DATABASE_DNS: sqlite:///database/database.db

SMTP_SERVER: SMTP server address
SMTP_SERVER_PORT: SMTP server port
SENDER_EMAIL_ADDRESS: Sending account address
SENDER_EMAIL_PASS: Sending account password

RECEIVER_EMAIL_ADDRESS: Email address of reciever 
```
<br>

# ▋Running the Bots

## Telegram Bot

To launch the Telegram bot, use:

```bash
python telegram_bot.py
```

## Avito Bot

To launch the Avito bot, use:

```bash

python avito_bot.py

```

To see logs without sending actual API calls, run the Avito bot in dry mode:

```bash
python avito_bot.py --dry
```

# ▋Running the Bots with docker 

## Telegram Bot

To launch the Telegram bot with docker, use:

```bash
docker compose -f docker-compose.telegram_bot.yml up
```

## Avito Bot

To launch the Avito bot with docker, use:

```bash
docker compose -f docker-compose.avito_bot.yml up
```

Nocodb will be available on localhost:8080. 
In it you need to add a new Data Source with 
the 'SQLite' Database Type and '/usr/src/app/database/< database file name >' SQLite File.