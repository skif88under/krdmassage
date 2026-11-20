import json
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

BASE_DIR = Path(__file__).resolve().parent.parent
order = 70
MENU_ITEMS = [{"text": "📢 Наш канал", "callback_data": "menu:channel"}]


async def setup(bot: Bot, dp: Dispatcher):
    @dp.callback_query(F.data == "menu:channel")
    async def channel(callback: CallbackQuery):
        with (BASE_DIR / "salon.json").open("r", encoding="utf-8") as file:
            url = json.load(file).get("channel_url", "")
        if url:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Перейти в канал", url=url)]
            ])
            await callback.message.answer("Подписывайтесь на наш канал:", reply_markup=keyboard)
        else:
            await callback.message.answer("Ссылка на канал пока не добавлена.")
        await callback.answer()
