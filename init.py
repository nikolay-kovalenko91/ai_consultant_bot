#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import telebot
from telebot import types

# Connect to bot
# Token placed in utils.py file. You can change it with your token
Bot = telebot.TeleBot(os.environ["BOT_TOKEN"])
print(
    f"The Bot is online (id: {Bot.get_me().id}) \33[0;31m[DEVELOPER"
    " MODE]\33[m..."
)

# Set bot commands
print("[!] Configuring bot commands...")
Bot.set_my_commands(
    commands=[
        types.BotCommand(command="start", description="Старт бота"),
        types.BotCommand(command="reset", description="Сбросить историю чата"),
    ]
)

print("[!] Commands successfully configured.\n[!] Run main.py")
