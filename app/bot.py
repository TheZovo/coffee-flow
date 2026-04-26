from __future__ import annotations

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.services.app_settings import get_app_settings, render_text
from app.services.users import get_or_create_user_by_telegram

customer_dp = Dispatcher()
customer_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None


def _name_from_message(message: Message) -> str | None:
    if not message.from_user:
        return None
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    return full_name or None


def _normalize_telegram_phone(phone: str | None) -> str | None:
    digits = "".join(char for char in (phone or "") if char.isdigit())
    if len(digits) < 8:
        return None
    return f"+{digits}"


async def _load_app_settings(session: AsyncSession | None = None):
    if session is not None:
        return await get_app_settings(session)

    async with SessionLocal() as local_session:
        return await get_app_settings(local_session)


def miniapp_keyboard(button_text: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(button_text or "☕ Открыть Coffee Flow").strip() or "☕ Открыть Coffee Flow",
                    web_app=WebAppInfo(url=settings.MINIAPP_URL),
                )
            ]
        ]
    )


async def send_to_user(chat_id: int, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    if customer_bot is None:
        return
    try:
        await customer_bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    except Exception:
        return


@customer_dp.message(CommandStart())
async def start_command(message: Message) -> None:
    app_settings = await _load_app_settings()
    await message.answer(
        render_text(app_settings.customer_start_text),
        reply_markup=miniapp_keyboard(app_settings.miniapp_button_text),
    )


@customer_dp.message(Command("app"))
async def app_command(message: Message) -> None:
    app_settings = await _load_app_settings()
    await message.answer(
        render_text(app_settings.customer_app_text),
        reply_markup=miniapp_keyboard(app_settings.miniapp_button_text),
    )


@customer_dp.message(Command("help"))
async def help_command(message: Message) -> None:
    app_settings = await _load_app_settings()
    await message.answer(
        render_text(app_settings.customer_help_text),
        reply_markup=miniapp_keyboard(app_settings.miniapp_button_text),
    )


@customer_dp.message(F.contact)
async def contact_command(message: Message) -> None:
    if not message.from_user or message.contact is None:
        return

    async with SessionLocal() as session:
        app_settings = await get_app_settings(session)

        if message.contact.user_id and message.contact.user_id != message.from_user.id:
            await message.answer(
                render_text(app_settings.customer_contact_request_text),
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        phone = _normalize_telegram_phone(message.contact.phone_number)
        if not phone:
            await message.answer(
                render_text(app_settings.customer_phone_error_text),
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        user = await get_or_create_user_by_telegram(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=_name_from_message(message),
        )
        user.phone = phone
        if not user.full_name:
            user.full_name = _name_from_message(message)
        await session.commit()

        await message.answer(
            render_text(app_settings.customer_phone_saved_text),
            reply_markup=miniapp_keyboard(app_settings.miniapp_button_text),
        )


dp = customer_dp
bot = customer_bot
