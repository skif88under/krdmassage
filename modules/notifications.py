import json
import logging
from pathlib import Path

from aiogram import Bot
from aiogram.types import User

from config import LOG_CHAT_ID

BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "new_users.json"


def _load_user_ids() -> set[int]:
    if not USERS_FILE.exists():
        return set()
    try:
        data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        return {int(user_id) for user_id in data.get("user_ids", [])}
    except (OSError, ValueError, TypeError, AttributeError) as error:
        logging.error("Не удалось прочитать new_users.json: %s", error)
        return set()


def _save_user_ids(user_ids: set[int]) -> None:
    temporary = USERS_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"user_ids": sorted(user_ids)}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    temporary.replace(USERS_FILE)


async def notify_new_user(bot: Bot, user: User) -> None:
    user_ids = _load_user_ids()
    if user.id in user_ids:
        return

    username = f"@{user.username}" if user.username else "не указан"
    full_name = " ".join(part for part in [user.first_name, user.last_name] if part)
    text = (
        "🆕 <b>Новый пользователь массажного бота</b>\n\n"
        f"Имя: {full_name or 'не указано'}\n"
        f"Username: {username}\n"
        f"Telegram ID: <code>{user.id}</code>"
    )

    try:
        await bot.send_message(LOG_CHAT_ID, text)
    except Exception:
        logging.exception("Не удалось отправить уведомление в чат %s", LOG_CHAT_ID)
        return

    user_ids.add(user.id)
    try:
        _save_user_ids(user_ids)
    except OSError:
        logging.exception("Уведомление отправлено, но не удалось сохранить ID пользователя")
