from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.models import Order, OrderStatus, User


def today_local_date():
    try:
        tz = ZoneInfo(settings.APP_TIMEZONE)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


async def find_order_by_number(
    session: AsyncSession,
    order_number: str,
    prefer_today: bool = True,
) -> Order | None:
    query = (
        select(Order)
        .options(joinedload(Order.user), joinedload(Order.branch), joinedload(Order.items))
        .where(Order.order_number == order_number)
        .order_by(Order.created_at.desc())
    )
    if prefer_today:
        today = today_local_date()
        today_result = await session.execute(query.where(Order.order_day == today))
        order = today_result.scalars().first()
        if order is not None:
            return order

    result = await session.execute(query)
    return result.scalars().first()


async def apply_order_status(
    session: AsyncSession,
    order: Order,
    new_status: OrderStatus,
) -> Order:
    old_status = order.status
    if old_status == new_status:
        return order

    user = order.user
    if user is None:
        user = await session.get(User, order.user_id)
        order.user = user

    if old_status == OrderStatus.CANCELLED and new_status != OrderStatus.CANCELLED and order.bonus_refunded:
        user.bonus_balance = max(0, user.bonus_balance - order.bonus_spent_cents)
        order.bonus_refunded = False

    if old_status == OrderStatus.COMPLETED and new_status != OrderStatus.COMPLETED and order.bonus_accrued:
        user.bonus_balance = max(0, user.bonus_balance - order.bonus_earned_cents)
        order.bonus_accrued = False

    if old_status == OrderStatus.COMPLETED and new_status != OrderStatus.COMPLETED and order.loyalty_reserved:
        user.loyalty_paid_coffee_count = max(0, user.loyalty_paid_coffee_count - order.loyalty_paid_coffee_count)
        user.loyalty_free_coffee_count = max(0, user.loyalty_free_coffee_count - order.loyalty_free_coffee_count)
        order.loyalty_reserved = False

    if new_status == OrderStatus.COMPLETED and not order.bonus_accrued:
        user.bonus_balance += order.bonus_earned_cents
        order.bonus_accrued = True

    if new_status == OrderStatus.COMPLETED and not order.loyalty_reserved:
        user.loyalty_paid_coffee_count += order.loyalty_paid_coffee_count
        user.loyalty_free_coffee_count += order.loyalty_free_coffee_count
        order.loyalty_reserved = True

    if new_status == OrderStatus.CANCELLED and old_status != OrderStatus.CANCELLED and not order.bonus_refunded:
        user.bonus_balance += order.bonus_spent_cents
        order.bonus_refunded = True

    order.status = new_status
    await session.commit()
    await session.refresh(order)
    return order
