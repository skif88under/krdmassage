import json
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

BASE_DIR = Path(__file__).resolve().parent.parent
order = 40
MENU_ITEMS = [{"text": "📍 Адрес и график", "callback_data": "menu:salon"}]


async def setup(bot: Bot, dp: Dispatcher):
    @dp.message(Command("salon"))
    async def salon_info(message: Message):
        with (BASE_DIR / "salon.json").open("r", encoding="utf-8") as file:
            data = json.load(file)
        text = (
            f"<b>{data.get('name', 'Массажный кабинет')}</b>\n\n"
            f"📍 Адрес: {data.get('address') or 'уточняется'}\n"
            f"🕒 График работы: {data.get('working_hours', 'уточняется')}"
        )
        if data.get("map_url"):
            text += f'\n🗺 <a href="{data["map_url"]}">Открыть карту</a>'
        if data.get("phone"):
            text += f'\n☎️ Телефон: {data["phone"]}'
        await message.answer(text, disable_web_page_preview=True)
