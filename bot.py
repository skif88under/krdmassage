import asyncio
import json
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

BASE_DIR = Path(__file__).resolve().parent


def load_json(filename: str):
    """Load a JSON data file from the same directory as bot.py."""
    path = BASE_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Не найден файл данных: {path}. "
            "Проверьте, что JSON-файл находится в корне репозитория рядом с bot.py."
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌿 Польза массажа")],
            [KeyboardButton(text="💆 Виды массажа"), KeyboardButton(text="🎁 Сертификаты")],
            [KeyboardButton(text="📝 Оставить заявку"), KeyboardButton(text="📍 Адрес и график")],
            [KeyboardButton(text="❓ Частые вопросы"), KeyboardButton(text="📢 Наш канал")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Главное меню")]],
        resize_keyboard=True,
    )


def service_keyboard(services: list) -> InlineKeyboardMarkup:
    buttons = []
    for service in services:
        if service.get("active", True):
            buttons.append([InlineKeyboardButton(
                text=service["name"],
                callback_data=f"service:{service['id']}"
            )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def faq_keyboard(faqs: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=item["question"], callback_data=f"faq:{i}")]
        for i, item in enumerate(faqs)
    ])


class Booking(StatesGroup):
    service = State()
    name = State()
    contact = State()


async def send_home(message: Message, state: FSMContext | None = None):
    if state:
        await state.clear()
    await message.answer(
        "Здравствуйте! 👋\n"
        "Добро пожаловать в пространство массажа, где главное — ваш комфорт, внимание к деталям и индивидуальный подход.\n"
        "В этом боте вы можете:\n\n"
        "💆‍♂️ **Виды массажа** — познакомиться с доступными техниками.\n"
        "🌿 **Польза массажа** — узнать больше о его возможностях.\n"
        "🎁 **Подарочные сертификаты** — выбрать подарок для близкого человека.\n"
        "📍 **Адрес и график** — спланировать свой визит.\n"
        "📝 **Запись на массаж** — оставить заявку в несколько нажатий.\n"
        "Выберите интересующий вас раздел ниже. Буду рад помочь вам подобрать подходящий вариант массажа. 🤝\n",
        reply_markup=main_menu(),
    )


async def main():
    token = os.getenv("BOT_TOKEN")
    admin_id_raw = os.getenv("ADMIN_ID")

    if not token:
        raise RuntimeError("Не задана переменная окружения BOT_TOKEN.")
    if not admin_id_raw or not admin_id_raw.isdigit():
        raise RuntimeError("Не задана переменная окружения ADMIN_ID (числовой Telegram ID владельца).")
    admin_id = int(admin_id_raw)

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message, state: FSMContext):
        await send_home(message, state)

    @dp.message(Command("cancel"))
    @dp.message(F.text == "⬅️ Главное меню")
    async def cancel_or_home(message: Message, state: FSMContext):
        await send_home(message, state)

    @dp.message(F.text == "💆 Виды массажа")
    async def services_list(message: Message):
        data = load_json("massages.json")
        services = [s for s in data.get("services", []) if s.get("active", True)]
        if not services:
            await message.answer("Список услуг пока заполняется.", reply_markup=main_menu())
            return
        await message.answer("Выберите услугу, чтобы посмотреть описание и цены:", reply_markup=service_keyboard(services))

    @dp.callback_query(Booking.service, F.data.startswith("service:"))
    async def booking_choose_service(callback: CallbackQuery, state: FSMContext):
        service_id = callback.data.split(":", 1)[1]
        services = load_json("massages.json").get("services", [])
        service = next((s for s in services if s["id"] == service_id and s.get("active", True)), None)
        if not service:
            await callback.answer("Услуга не найдена.", show_alert=True)
            return
        await state.update_data(service_id=service_id, service_name=service["name"])
        await state.set_state(Booking.name)
        await callback.message.answer("Как вас зовут?", reply_markup=back_keyboard())
        await callback.answer()


    @dp.callback_query(F.data.startswith("service:"))
    async def service_detail(callback: CallbackQuery):
        service_id = callback.data.split(":", 1)[1]
        data = load_json("massages.json")
        service = next((s for s in data.get("services", []) if s["id"] == service_id and s.get("active", True)), None)
        if not service:
            await callback.answer("Услуга не найдена.", show_alert=True)
            return
        course = service.get("course_price")
        course_text = f"{course} ₽" if course not in (None, "") else "Уточняйте у мастера"
        text = (
            f"<b>{service['name']}</b>\n\n"
            f"{service.get('description', 'Описание скоро появится.')}\n\n"
            f"⏱ Длительность: {service.get('duration_minutes', 'уточняется')} мин.\n"
            f"💳 Один сеанс: {service.get('session_price', 'уточняется')} ₽\n"
            f"📦 Курс: {course_text}"
        )
        await callback.message.answer(text, reply_markup=main_menu())
        await callback.answer()

    @dp.message(F.text == "🎁 Сертификаты")
    async def certificates(message: Message):
        data = load_json("certificates.json")
        text = data.get("text", "Информация о подарочных сертификатах скоро появится.")
        options = data.get("options", [])
        if options:
            text += "\n\n" + "\n".join(f"• {item}" for item in options)
        await message.answer(text, reply_markup=main_menu())

    @dp.message(F.text == "📍 Адрес и график")
    async def contacts(message: Message):
        data = load_json("salon.json")
        text = (
            f"<b>{data.get('name', 'Массажный салон')}</b>\n\n"
            f"📍 Адрес: {data.get('address', 'уточняется')}\n"
            f"🕒 График работы: {data.get('working_hours', 'уточняется')}"
        )
        if data.get("map_url"):
            text += f"\n🗺 <a href=\"{data['map_url']}\">Открыть карту</a>"
        if data.get("phone"):
            text += f"\n☎️ Телефон: {data['phone']}"
        await message.answer(text, reply_markup=main_menu(), disable_web_page_preview=True)

    @dp.message(F.text == "❓ Частые вопросы")
    async def faq_list(message: Message):
        data = load_json("faqs.json")
        faqs = data.get("faqs", [])
        if not faqs:
            await message.answer("Раздел вопросов пока заполняется.", reply_markup=main_menu())
            return
        await message.answer("Выберите вопрос:", reply_markup=faq_keyboard(faqs))

    @dp.callback_query(F.data.startswith("faq:"))
    async def faq_answer(callback: CallbackQuery):
        try:
            index = int(callback.data.split(":", 1)[1])
            faqs = load_json("faqs.json").get("faqs", [])
            item = faqs[index]
            await callback.message.answer(
                f"<b>{item['question']}</b>\n\n{item['answer']}",
                reply_markup=main_menu()
            )
        except (ValueError, IndexError, KeyError):
            await callback.answer("Вопрос не найден.", show_alert=True)
            return
        await callback.answer()

    @dp.message(F.text == "🌿 Польза массажа")
    async def massage_benefits(message: Message):
        text = (
            "<b>🌿 Польза массажа</b>\n\n"
            "Массаж — это возможность уделить время себе, расслабиться и почувствовать лёгкость в теле.\n\n"
            "✨ <b>Что может дать массаж:</b>\n\n"
            "🧘 <b>Снятие стресса</b> — помогает расслабиться и отдохнуть.\n"
            "💆 <b>Снижение мышечного напряжения</b> — способствует расслаблению уставших мышц.\n"
            "❤️ <b>Местное кровообращение</b> — массаж стимулирует кровоток в массируемых тканях.\n"
            "🌿 <b>Поддержка лимфооттока</b> — некоторые техники помогают движению лимфы.\n"
            "🤲 <b>Облегчение мышечного дискомфорта</b> — может уменьшать ощущение скованности и болезненности.\n"
            "😌 <b>Расслабление и спокойствие</b> — может способствовать снижению ощущения тревоги.\n"
            "🌙 <b>Отдых и сон</b> — расслабление после массажа может помочь лучше отдохнуть.\n"
            "💚 <b>Забота о себе</b> — возможность уделить внимание своему телу и самочувствию.\n\n"
            "Выберите подходящий массаж и оставьте заявку — мастер свяжется с вами. 💚\n\n"
        )
        await message.answer(text, reply_markup=main_menu())

    @dp.message(F.text == "📢 Наш канал")
    async def channel(message: Message):
        url = load_json("salon.json").get("channel_url", "")
        if url:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Перейти в канал", url=url)]
            ])
            await message.answer("Подписывайтесь на наш канал:", reply_markup=kb)
        else:
            await message.answer("Ссылка на канал пока не добавлена.", reply_markup=main_menu())

    @dp.message(F.text == "📝 Оставить заявку")
    async def booking_start(message: Message, state: FSMContext):
        data = load_json("massages.json")
        services = [s for s in data.get("services", []) if s.get("active", True)]
        if not services:
            await message.answer("Пока нельзя оставить заявку: список услуг ещё не заполнен.", reply_markup=main_menu())
            return
        await state.clear()
        await state.set_state(Booking.service)
        await message.answer("Выберите вид массажа:", reply_markup=service_keyboard(services))

    @dp.message(Booking.name, F.text)
    async def booking_name(message: Message, state: FSMContext):
        name = message.text.strip()
        if name == "⬅️ Главное меню":
            await send_home(message, state)
            return
        if len(name) < 2:
            await message.answer("Пожалуйста, укажите имя.")
            return
        await state.update_data(client_name=name)
        await state.set_state(Booking.contact)
        await message.answer(
            "Оставьте номер телефона или другой удобный способ связи.\n"
            "Например: +7 900 000-00-00 или @username",
            reply_markup=back_keyboard()
        )

    @dp.message(Booking.contact, F.text)
    async def booking_contact(message: Message, state: FSMContext):
        contact = message.text.strip()
        if contact == "⬅️ Главное меню":
            await send_home(message, state)
            return
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
            await bot.send_message(admin_id, request_text)
        except Exception:
            logging.exception("Не удалось отправить заявку администратору")
            await message.answer(
                "Не удалось отправить заявку автоматически. Попробуйте позже или свяжитесь с мастером напрямую.",
                reply_markup=main_menu()
            )
            await state.clear()
            return

        await message.answer(
            "Спасибо! Заявка отправлена мастеру. Он свяжется с вами по указанным контактам.",
            reply_markup=main_menu()
        )
        await state.clear()

    @dp.message()
    async def fallback(message: Message):
        await message.answer("Пожалуйста, выберите раздел в меню или отправьте /start.", reply_markup=main_menu())


    @dp.errors()
    async def errors_handler(event):
        logging.exception("Ошибка при обработке обновления: %s", event.exception)
        return True

    logging.basicConfig(level=logging.INFO)
    logging.info("Бот запущен. Ожидание сообщений...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
