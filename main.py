import asyncio
import json
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, BotCommand, MenuButtonCommands, FSInputFile

from config import BOT_TOKEN
from core.loader import load_modules
from modules.notifications import notify_new_user

BASE_DIR = Path(__file__).resolve().parent


def load_settings():
    with (BASE_DIR / "settings.json").open("r", encoding="utf-8") as file:
        return json.load(file)


async def main():
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    commands = [
        BotCommand(command="services", description="Виды массажа"),
        BotCommand(command="booking", description="Оставить заявку"),
        BotCommand(command="certificates", description="Подарочные сертификаты"),
        BotCommand(command="salon", description="Адрес и график работы"),
        BotCommand(command="faq", description="Частые вопросы"),
        BotCommand(command="benefits", description="Польза массажа"),
        BotCommand(command="channel", description="Наш канал"),
    ]

    try:
        await load_modules(bot, dp)
        await bot.set_my_commands(commands)
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
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
                        caption=welcome_text
                    )
                    return
                logging.warning("Приветственное изображение не найдено: %s", image_path)
            await message.answer(welcome_text)

        logging.info("Массажный бот запущен")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
