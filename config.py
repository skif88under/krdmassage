import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID")
LOG_CHAT_ID_RAW = os.getenv("LOG_CHAT_ID")

if not BOT_TOKEN:
    raise RuntimeError("Не задана переменная окружения BOT_TOKEN.")

if not ADMIN_ID_RAW or not ADMIN_ID_RAW.lstrip("-").isdigit():
    raise RuntimeError("Не задана переменная окружения ADMIN_ID (числовой Telegram ID владельца).")

if not LOG_CHAT_ID_RAW or not LOG_CHAT_ID_RAW.lstrip("-").isdigit():
    raise RuntimeError("Не задана переменная окружения LOG_CHAT_ID (числовой ID отдельного Telegram-чата).")

ADMIN_ID = int(ADMIN_ID_RAW)
LOG_CHAT_ID = int(LOG_CHAT_ID_RAW)
