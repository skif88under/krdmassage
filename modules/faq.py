import json
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

BASE_DIR = Path(__file__).resolve().parent.parent
order = 50
MENU_ITEMS = [{"text": "❓ Частые вопросы", "callback_data": "menu:faq"}]


async def setup(bot: Bot, dp: Dispatcher):
    @dp.message(Command("faq"))
    async def faq_list(message: Message):
        with (BASE_DIR / "faqs.json").open("r", encoding="utf-8") as file:
            faqs = json.load(file).get("faqs", [])
        if not faqs:
            await message.answer("Раздел вопросов пока заполняется.")
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=item["question"], callback_data=f"faq:{index}")]
                for index, item in enumerate(faqs)
            ])
            await message.answer("Выберите вопрос:", reply_markup=keyboard)

    @dp.callback_query(F.data.startswith("faq:"))
    async def faq_answer(callback: CallbackQuery):
        try:
            index = int(callback.data.split(":", 1)[1])
            with (BASE_DIR / "faqs.json").open("r", encoding="utf-8") as file:
                faqs = json.load(file).get("faqs", [])
            item = faqs[index]
            await callback.message.answer(f"<b>{item['question']}</b>\n\n{item['answer']}")
        except (ValueError, IndexError, KeyError):
            await callback.answer("Вопрос не найден.", show_alert=True)
            return
        await callback.answer()
