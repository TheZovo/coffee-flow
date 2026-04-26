from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.models import BaristaShift, User

WEEKDAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def barista_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.APP_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def barista_now() -> datetime:
    return datetime.now(barista_timezone())


def weekday_label(weekday: int | None) -> str:
    if weekday is None:
        return ""
    normalized = max(0, min(6, int(weekday)))
    return WEEKDAY_LABELS[normalized]


def format_shift_datetime(shift: BaristaShift | None) -> str:
    if shift is None:
        return ""
    return f"{weekday_label(shift.weekday)} {shift.start_time.strftime('%H:%M')}"


def format_shift_range(shift: BaristaShift | None) -> str:
    if shift is None:
        return ""
    return f"{weekday_label(shift.weekday)} {shift.start_time.strftime('%H:%M')} - {shift.end_time.strftime('%H:%M')}"


def normalize_barista_username(username: str | None) -> str | None:
    normalized = (username or "").strip().lstrip("@").lower()
    return normalized or None


def normalize_barista_full_name(full_name: str | None) -> str | None:
    normalized = " ".join(str(full_name or "").split())
    return normalized or None


def is_placeholder_telegram_id(telegram_id: int | None) -> bool:
    return int(telegram_id or 0) < 0


def _shift_sort_key(shift: BaristaShift) -> tuple[int, str, int]:
    return (int(shift.weekday), shift.start_time.isoformat(), int(shift.id))


def _is_shift_active(shift: BaristaShift, current: datetime) -> bool:
    if not shift.is_active:
        return False
    if int(shift.weekday) != current.weekday():
        return False
    current_time = current.timetz().replace(tzinfo=None)
    return shift.start_time <= current_time < shift.end_time


def _shift_next_start(shift: BaristaShift, current: datetime) -> datetime:
    days_ahead = (int(shift.weekday) - current.weekday()) % 7
    candidate_day = current.date() + timedelta(days=days_ahead)
    candidate = datetime.combine(candidate_day, shift.start_time, tzinfo=current.tzinfo)
    if candidate <= current:
        candidate += timedelta(days=7)
    return candidate


def _find_active_shift(shifts: list[BaristaShift], current: datetime) -> BaristaShift | None:
    active = [shift for shift in shifts if _is_shift_active(shift, current)]
    if not active:
        return None
    return sorted(active, key=_shift_sort_key)[0]


def _find_next_shift(shifts: list[BaristaShift], current: datetime) -> BaristaShift | None:
    upcoming = [shift for shift in shifts if shift.is_active]
    if not upcoming:
        return None
    return min(upcoming, key=lambda shift: (_shift_next_start(shift, current), *_shift_sort_key(shift)))


@dataclass(slots=True)
class BaristaAccessState:
    user: User | None
    active_shift: BaristaShift | None
    next_shift: BaristaShift | None

    @property
    def is_registered(self) -> bool:
        return self.user is not None and bool(self.user.is_barista)

    @property
    def can_access(self) -> bool:
        return self.is_registered and self.active_shift is not None


async def claim_pending_barista_profile(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str | None,
) -> bool:
    current_user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    normalized_username = normalize_barista_username(username)
    normalized_full_name = normalize_barista_full_name(full_name)

    pending_candidate: User | None = None
    if normalized_username:
        username_matches = (
            await session.execute(
                select(User)
                .options(joinedload(User.barista_shifts))
                .where(
                    User.is_barista.is_(True),
                    User.telegram_id < 0,
                    func.lower(User.username) == normalized_username,
                )
                .order_by(User.id.asc())
            )
        ).unique().scalars().all()
        if len(username_matches) == 1:
            pending_candidate = username_matches[0]

    if pending_candidate is None and normalized_full_name:
        full_name_matches = (
            await session.execute(
                select(User)
                .options(joinedload(User.barista_shifts))
                .where(
                    User.is_barista.is_(True),
                    User.telegram_id < 0,
                    or_(User.username.is_(None), User.username == ""),
                    func.lower(User.full_name) == normalized_full_name.lower(),
                )
                .order_by(User.id.asc())
            )
        ).unique().scalars().all()
        if len(full_name_matches) == 1:
            pending_candidate = full_name_matches[0]

    if pending_candidate is None:
        return False

    if current_user is None:
        pending_candidate.telegram_id = telegram_id
        if normalized_username:
            pending_candidate.username = normalized_username
        if normalized_full_name:
            pending_candidate.full_name = normalized_full_name
        return True

    if current_user.id == pending_candidate.id:
        return False

    current_user.is_barista = True
    if normalized_username:
        current_user.username = normalized_username
    elif pending_candidate.username and not current_user.username:
        current_user.username = pending_candidate.username
    if normalized_full_name:
        current_user.full_name = normalized_full_name
    elif pending_candidate.full_name and not current_user.full_name:
        current_user.full_name = pending_candidate.full_name

    for shift in list(pending_candidate.barista_shifts):
        shift.user = current_user

    await session.delete(pending_candidate)
    return True


async def get_barista_access_state(session: AsyncSession, telegram_id: int) -> BaristaAccessState:
    user = await session.scalar(
        select(User)
        .options(joinedload(User.barista_shifts))
        .where(User.telegram_id == telegram_id)
    )
    if user is None or not user.is_barista:
        return BaristaAccessState(user=user, active_shift=None, next_shift=None)

    now = barista_now()
    shifts = sorted(list(user.barista_shifts or []), key=_shift_sort_key)
    active_shift = _find_active_shift(shifts, now)
    next_shift = _find_next_shift(shifts, now)
    return BaristaAccessState(user=user, active_shift=active_shift, next_shift=next_shift)


async def get_active_barista_chat_ids(session: AsyncSession) -> set[int]:
    now = barista_now()
    current_time = now.timetz().replace(tzinfo=None)
    result = await session.execute(
        select(User.telegram_id)
        .join(BaristaShift, BaristaShift.user_id == User.id)
        .where(
            User.is_barista.is_(True),
            User.telegram_id > 0,
            BaristaShift.is_active.is_(True),
            BaristaShift.weekday == now.weekday(),
            BaristaShift.start_time <= current_time,
            BaristaShift.end_time > current_time,
        )
        .distinct()
    )
    return {int(value) for value in result.scalars().all()}
