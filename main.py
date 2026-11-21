import asyncio
import json
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile

from config import BOT_TOKEN
from core.loader import load_modules
from modules.notifications import notify_new_user

BASE_DIR = Path(__file__).resolve().parent


def load_settings():
    with (BASE_DIR / "settings.json").open("r", encoding="utf-8") as file:
        return json.load(file)


def build_menu(items):
    buttons = [KeyboardButton(text=item["text"]) for item in items]

    # Первые три кнопки — в одной строке, остальные — по одной.
    rows = []
    if buttons:
        rows.append(buttons[:3])
        rows.extend([[button] for button in buttons[3:]])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=False,
        input_field_placeholder="Выберите раздел меню"
    ) if rows else None


async def main():
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    try:
        menu_items = await load_modules(bot, dp)
        menu = build_menu(menu_items)
        welcome_text = settings.get("welcome_text", "Здравствуйте! Добро пожаловать.")

        @dp.message(CommandStart())
        async def start_handler(message: Message):
            if message.from_user:
                await notify_new_user(bot, message.from_user)

            image_name = settings.get("welcome_image")
            if image_name:
                image_path = BASE_DIR / image_name
                if image_path.is_file():
                    await message.answer_photo(
                        photo=FSInputFile(image_path),
                        caption=welcome_text,
                        reply_markup=menu
                    )
                    return
                logging.warning("Приветственное изображение не найдено: %s", image_path)
            await message.answer(welcome_text, reply_markup=menu)

        logging.info("Массажный бот запущен")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
