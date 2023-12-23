#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
from telebot import types
from constants import TELEGRAM_BOT_TOKEN
import logging

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


# Connect to bot
# Token placed in utils.py file. You can change it with your token
Bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
logging.info(
    f"The Bot is online (id: {Bot.get_me().id}) \33[0;31m[DEVELOPER"
    " MODE]\33[m..."
)

# Set bot commands
logging.info("[!] Configuring bot commands...")
Bot.set_my_commands(
    commands=[
        types.BotCommand(command="start", description="Старт бота"),
        types.BotCommand(command="reset", description="Сбросить историю чата"),
    ]
)

logging.info("[!] Commands successfully configured.\n[!] Run main.py")
