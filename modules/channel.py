import json
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

BASE_DIR = Path(__file__).resolve().parent.parent
order = 70
MENU_ITEMS = [{"text": "📢 Наш канал", "callback_data": "menu:channel"}]


async def setup(bot: Bot, dp: Dispatcher):
    @dp.message(Command("channel"))
    async def channel(message: Message):
        with (BASE_DIR / "salon.json").open("r", encoding="utf-8") as file:
            url = json.load(file).get("channel_url", "")
        if url:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Перейти в канал", url=url)]
            ])
            await message.answer("Подписывайтесь на наш канал:", reply_markup=keyboard)
        else:
            await message.answer("Ссылка на канал пока не добавлена.")
