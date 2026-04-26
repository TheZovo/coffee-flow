from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot import miniapp_keyboard, send_to_user
from app.config import settings
from app.models import AppSettings, Order, User
from app.services.app_settings import get_app_settings

logger = logging.getLogger("coffeeflow.reminders")

DEFAULT_REMINDER_TEXT = (
    "Мы давно вас не видели. Загляните в Coffee Flow и соберите новый заказ."
)


def app_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.APP_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def now_local() -> datetime:
    return datetime.now(app_timezone())


def parse_reminder_time(value: str | None) -> time:
    raw = (value or "").strip()
    try:
        hour_text, minute_text = raw.split(":", 1)
        parsed = time(hour=int(hour_text), minute=int(minute_text))
    except (ValueError, TypeError):
        parsed = time(hour=12, minute=0)
    return parsed


def reminder_preview(app_settings: AppSettings) -> str:
    if not app_settings.inactive_reminder_enabled:
        return "Напоминания выключены."
    return (
        f"Напоминания уходят пользователям без заказов {app_settings.inactive_reminder_days} дн. "
        f"в {app_settings.inactive_reminder_send_time}."
    )


def _last_run_local_date(app_settings: AppSettings) -> date | None:
    if app_settings.inactive_reminder_last_run_at is None:
        return None
    return app_settings.inactive_reminder_last_run_at.astimezone(app_timezone()).date()


def should_run_reminders(app_settings: AppSettings, current: datetime | None = None) -> bool:
    if not app_settings.inactive_reminder_enabled:
        return False
    current = current or now_local()
    scheduled_time = parse_reminder_time(app_settings.inactive_reminder_send_time)
    if current.time().replace(second=0, microsecond=0) < scheduled_time:
        return False
    if _last_run_local_date(app_settings) == current.date():
        return False
    reminder_text = (app_settings.inactive_reminder_text or "").strip()
    return bool(reminder_text)


async def _load_eligible_users(session: AsyncSession, inactive_days: int, current: datetime) -> list[User]:
    threshold = current - timedelta(days=max(1, inactive_days))
    last_order_subquery = (
        select(Order.user_id.label("user_id"), func.max(Order.created_at).label("last_order_at"))
        .group_by(Order.user_id)
        .subquery()
    )
    activity_at = func.coalesce(last_order_subquery.c.last_order_at, User.created_at)
    result = await session.execute(
        select(User)
        .outerjoin(last_order_subquery, last_order_subquery.c.user_id == User.id)
        .where(
            User.is_barista.is_(False),
            User.telegram_id > 0,
            activity_at <= threshold,
            or_(
                User.inactive_reminder_sent_at.is_(None),
                User.inactive_reminder_sent_at < activity_at,
            ),
        )
        .order_by(activity_at.asc(), User.id.asc())
    )
    return result.scalars().all()


async def run_inactive_reminders_once(
    session_factory: async_sessionmaker[AsyncSession],
    current: datetime | None = None,
) -> int:
    current = current or now_local()
    async with session_factory() as session:
        app_settings = await get_app_settings(session)
        if not should_run_reminders(app_settings, current):
            return 0

        recipients = await _load_eligible_users(
            session,
            inactive_days=app_settings.inactive_reminder_days,
            current=current,
        )
        if not recipients:
            app_settings.inactive_reminder_last_run_at = current
            await session.commit()
            return 0

        reminder_text = (app_settings.inactive_reminder_text or "").strip() or DEFAULT_REMINDER_TEXT
        sent_count = 0
        for user in recipients:
            try:
                await send_to_user(
                    user.telegram_id,
                    reminder_text,
                    reply_markup=miniapp_keyboard(app_settings.miniapp_button_text),
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to send inactivity reminder to %s: %s", user.telegram_id, exc)
                continue
            user.inactive_reminder_sent_at = current
            sent_count += 1

        app_settings.inactive_reminder_last_run_at = current
        await session.commit()
        return sent_count
