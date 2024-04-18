from dataclasses import dataclass
import telebot


@dataclass
class BotInfo:
    id: int
    instance: telebot.TeleBot
    prompt: str
    offset: int = 0
