import json
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_ID

BASE_DIR = Path(__file__).resolve().parent.parent
order = 20
MENU_ITEMS = [{"text": "📝 Оставить заявку", "callback_data": "menu:booking"}]


class Booking(StatesGroup):
    name = State()
    contact = State()


def get_services():
    with (BASE_DIR / "massages.json").open("r", encoding="utf-8") as file:
        return json.load(file).get("services", [])


async def setup(bot: Bot, dp: Dispatcher):
    @dp.message(Command("booking"))
    async def booking_start(message: Message):
        services = [item for item in get_services() if item.get("active", True)]
        if not services:
            await message.answer("Пока нельзя оставить заявку: список услуг ещё заполняется.")
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=item["name"], callback_data=f"book:{item['id']}")]
                for item in services
            ])
            await message.answer("Выберите вид массажа:", reply_markup=keyboard)

    @dp.callback_query(F.data.startswith("book:"))
    async def booking_choose_service(callback: CallbackQuery, state: FSMContext):
        service_id = callback.data.split(":", 1)[1]
        service = next(
            (item for item in get_services()
             if item.get("id") == service_id and item.get("active", True)),
            None
        )
        if not service:
            await callback.answer("Услуга не найдена или временно недоступна.", show_alert=True)
            return

        await state.clear()
        await state.update_data(service_id=service_id, service_name=service["name"])
        await state.set_state(Booking.name)
        await callback.message.answer("Как вас зовут? Для отмены отправьте /cancel.")
        await callback.answer()

    @dp.message(Command("cancel"))
    async def booking_cancel(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Заявка отменена. Откройте меню через кнопку слева от строки ввода.")

    @dp.message(Booking.name, F.text)
    async def booking_name(message: Message, state: FSMContext):
        name = message.text.strip()
        if len(name) < 2:
            await message.answer("Пожалуйста, укажите имя.")
            return
        await state.update_data(client_name=name)
        await state.set_state(Booking.contact)
        await message.answer(
            "Оставьте номер телефона или другой удобный способ связи.\n"
            "Например: +7 900 000-00-00 или @username"
        )

    @dp.message(Booking.contact, F.text)
    async def booking_contact(message: Message, state: FSMContext):
        contact = message.text.strip()
        if len(contact) < 4:
            await message.answer("Пожалуйста, укажите корректный контакт для связи.")
            return

        data = await state.get_data()
        user = message.from_user
        username = f"@{user.username}" if user and user.username else "не указан"
        user_id = user.id if user else "неизвестен"
        request_text = (
            "🆕 <b>Новая заявка на массаж</b>\n\n"
            f"💆 Услуга: {data.get('service_name', 'не указана')}\n"
            f"👤 Имя: {data.get('client_name', 'не указано')}\n"
            f"📞 Контакт: {contact}\n"
            f"🔗 Telegram: {username}\n"
            f"🆔 Telegram ID: <code>{user_id}</code>"
        )
        try:
            await bot.send_message(ADMIN_ID, request_text)
        except Exception:
            logging.exception("Не удалось отправить заявку администратору")
            await message.answer("Не удалось отправить заявку. Попробуйте позже или свяжитесь с мастером напрямую.")
            await state.clear()
            return

        await message.answer("Спасибо! Заявка отправлена мастеру. Он свяжется с вами по указанным контактам.")
        await state.clear()
