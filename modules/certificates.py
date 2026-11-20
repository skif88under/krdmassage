import json
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery

BASE_DIR = Path(__file__).resolve().parent.parent
order = 30
MENU_ITEMS = [{"text": "🎁 Сертификаты", "callback_data": "menu:certificates"}]


async def setup(bot: Bot, dp: Dispatcher):
    @dp.callback_query(F.data == "menu:certificates")
    async def certificates(callback: CallbackQuery):
        with (BASE_DIR / "certificates.json").open("r", encoding="utf-8") as file:
            data = json.load(file)
        text = data.get("text", "Информация о подарочных сертификатах скоро появится.")
        options = data.get("options", [])
        if options:
            text += "\n\n" + "\n".join(f"• {item}" for item in options)
        await callback.message.answer(text)
        await callback.answer()
