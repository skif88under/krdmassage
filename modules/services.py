import json
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

BASE_DIR = Path(__file__).resolve().parent.parent
order = 10
MENU_ITEMS = [{"text": "💆 Виды массажа", "callback_data": "menu:services"}]


def get_services():
    with (BASE_DIR / "massages.json").open("r", encoding="utf-8") as file:
        return json.load(file).get("services", [])


async def setup(bot: Bot, dp: Dispatcher):
    @dp.message(F.text == "💆 Виды массажа")
    async def services_list(message: Message):
        services = [item for item in get_services() if item.get("active", True)]
        if not services:
            await message.answer("Список услуг пока заполняется.")
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=item["name"], callback_data=f"service:{item['id']}")]
                for item in services
            ])
            await message.answer("Выберите услугу:", reply_markup=keyboard)

    @dp.callback_query(F.data.startswith("service:"))
    async def service_detail(callback: CallbackQuery):
        service_id = callback.data.split(":", 1)[1]
        service = next(
            (item for item in get_services()
             if item.get("id") == service_id and item.get("active", True)),
            None
        )
        if not service:
            await callback.answer("Услуга не найдена или временно недоступна.", show_alert=True)
            return

        course = service.get("course_price")
        course_text = f"{course} ₽" if course not in (None, "", 0) else "Уточняйте у мастера"
        text = (
            f"<b>{service['name']}</b>\n\n"
            f"{service.get('description', 'Описание скоро появится.')}\n\n"
            f"⏱ Длительность: {service.get('duration_minutes', 'уточняется')} мин.\n"
            f"💳 Один сеанс: {service.get('session_price', 'уточняется')} ₽\n"
            f"📦 Курс: {course_text}"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data=f"book:{service_id}")]
        ])
        await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()
