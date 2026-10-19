# Consultant bot

Automated small business conversations on Telegram and Avito  to answer recurring questions with human
follow-up. The application uses configurable prompts, account-specific Avito
FAQs, saved conversation history, and the external OpenAI API.

The next milestone replaces growing FAQ
prompts with retrieval of relevant business knowledge, then adds an explicit
conversation workflow, bounded API failures, metrics, and offline regression
checks. A separate deployment package will add Docker Hub image publication and
manual SSH deployment to one server. These changes are planned, not implemented.

## Anything Else

I created this product initiative and want to resume development. The remaining work is an estimated
30–40 hours for the initial development milestone, with estimates refined during
implementation. This is a planning estimate, not a delivery commitment or a limit
on further development.

Completed licensing/documentation preparation, configuration hygiene, and existing
style-check CI are excluded. Docker Hub publication and SSH deployment remain
future work. The [roadmap](../ROADMAP.md) and
[development plan](DEVELOPMENT_PLAN.md) describe priorities, dependencies, scope
boundaries, and completion checks.

Retrieving relevant knowledge requires changes across account configuration,
message handlers, conversation state, and API integration. I'll update the legacy
SDK, make retrieval and fallback transitions explicit with LangGraph, add
OpenTelemetry metrics, and support manual deployment and rollback on one prepared
server. The application calls the external OpenAI API; this work does not host or
train a model.

I'll use synthetic knowledge and mocked services to check isolation, reindexing,
persistence, source propagation, fallback routing, bounded failures, and metrics.
Default tests will need no live credentials or outbound messages. The demo will
distinguish mocked flow from real API behavior; remote deployment and AWS delivery
will remain unverified until actually tested.

## What exists

- Multiple database-configured Telegram bot and Avito accounts, each with an
  assigned prompt. Both bot account queries select active accounts.
- Telegram text replies, `/start`, and `/reset`. Reset expects the conversation
  history file to exist; use `/start` before resetting a new conversation.
- Avito polling of unread chats, replies, and account-specific FAQ records
  appended in full to the prompt. There is no document retrieval index.
- JSON conversation history. Telegram bot history includes the bot account ID;
  Avito history uses the chat ID, and Telegram client history uses the sender
  ID. These paths do not all provide explicit account isolation yet.
- Email notification when the shared handler detects a supported phone-number
  pattern, followed by a closing reply. Avito also forwards non-text-message
  follow-up information by email; the Telegram bot loop only handles text.
- Separate TDLib-based Telegram user-account clients, including interactive
  registration, private-message prompts, and keyword-filtered group replies.
  Their account loader does not currently filter `is_active`.

See [the development plan](docs/DEVELOPMENT_PLAN.md) for the remaining behavior
and isolation work. Existing history is file-based; SQLAlchemy stores account,
prompt, and Avito FAQ configuration rather than conversation messages.

## Current stack

Python, pyTelegramBotAPI, requests, SQLAlchemy, SQLite by default,
python-dotenv, SMTP via Python's standard library, and `openai==0.28` using
`openai.ChatCompletion.create`. `secure-smtplib` is also listed in
[requirements.txt](requirements.txt). The generation model is currently
hardcoded as `gpt-4o-mini` in [constants.py](constants.py), not read from an
environment variable. Docker Compose includes NocoDB for editing the database.
The optional Telegram clients load native TDLib binaries from `tc/libs`.

ChromaDB, LangGraph, and OpenTelemetry are planned additions. No implementation
was found in the available local branches or remote-tracking branch tips.
Other unpublished branches or related repositories were not inspected.

## Local setup

Use Python 3.11 to match the Docker image. CI currently checks formatting on
Python 3.10. Install Git and, for the container path, Docker with Compose v2.
Live operation needs OpenAI access, the selected channel's credentials, and
working SMTP credentials for contact notifications. There is no credential-free
offline demo in the current application.

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
mkdir -p database history telegram_client_sessions
```

Replace the placeholders in `.env` before using a live service.
[constants.py](constants.py) loads it through python-dotenv. `OPENAI_API_KEY`,
`SYSTEM_PROMPT`, `SENDER_EMAIL_ADDRESS`, `SENDER_EMAIL_PASS`, and
`RECEIVER_EMAIL_ADDRESS` are required at import time, even for paths that do
not send email. `SYSTEM_PROMPT` remains a required legacy default although
normal account replies receive a database prompt. The remaining variables and
current defaults are listed in [.env.example](.env.example); the spelling
`DATABASE_DNS` matches the code.

### Initialize and configure accounts

With `.env` filled in and the directories created, initialize empty tables:

```bash
python -c 'import database'
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

Run registration interactively first. It asks for the phone number, Telegram
`api_id`, `api_hash`, login code, and any two-factor password, and stores the
account and session locally. Set the account's `private_message_prompt_id`,
`group_message_prompt_id`, and comma-separated `keywords` as needed. Group
responses require matching keywords and a group prompt. Stop registration with
Ctrl-C when finished; its input loop continues for additional accounts.

## Running the Bots with Docker

Complete `.env` and initialize/configure the local database as above, then start
the two bot services and database editor:

```bash
docker compose -f docker-compose up --build
```

Nocodb will be available on localhost:8080. 
In it you need to add a new Data Source with 
the 'SQLite' Database Type and '/usr/src/app/database/< database file name >' SQLite File.

Open [local NocoDB](http://localhost:8080), complete its setup, and add a SQLite
data source at `/usr/src/app/database/database.db`. This is the container path
for the default database. Keep this local administration service private.
Create a `prompts` row with `name` and `text`, then one of:
- `telegram_accounts`: `token`, optional `name`, `prompt_id`, and `is_active`.
- `avito_accounts`: `user_id`, `client_id`, `client_secret`, optional `name`,
  `prompt_id`, and `is_active`. Optional `faq` rows use this account's database
  `id` as `account_id` and contain `question` and `answer`.

## License

The owner's selected project license is **MPL-2.0**; the complete, unmodified
text is in [LICENSE](LICENSE). Existing code has multiple contributors, and
permission to apply MPL notices to their contributions has not been established
by this preparation. 
