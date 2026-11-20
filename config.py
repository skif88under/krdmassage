import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("Не задана переменная окружения BOT_TOKEN.")

if not ADMIN_ID_RAW or not ADMIN_ID_RAW.isdigit():
    raise RuntimeError("Не задана переменная окружения ADMIN_ID (числовой Telegram ID владельца).")

ADMIN_ID = int(ADMIN_ID_RAW)
