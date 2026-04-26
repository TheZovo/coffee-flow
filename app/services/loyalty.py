from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LoyaltySettings, Product, User

DEFAULT_LOYALTY_CATEGORY_SLUG = "coffee"
DEFAULT_LOYALTY_PAID_ITEMS_PER_REWARD = 5
DEFAULT_BONUS_EARN_PERCENT = 5
DEFAULT_BONUS_REDEEM_MAX_PERCENT = 100
LOYALTY_SETTINGS_SINGLETON_ID = 1


def normalize_loyalty_category_slug(value: str | None) -> str:
    slug = (value or "").strip().lower().replace("_", "-")
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^\w-]+", "", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug


def normalize_loyalty_category_slugs(values: list[str] | tuple[str, ...] | str | None) -> list[str]:
    if values is None:
        raw_values: list[str] = []
    elif isinstance(values, str):
        raw_values = re.split(r"[,\n;]+", values)
    else:
        raw_values = [str(item) for item in values]

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in raw_values:
        slug = normalize_loyalty_category_slug(raw_value)
        if not slug or slug in seen:
            continue
        normalized.append(slug)
        seen.add(slug)

    return normalized


def serialize_loyalty_category_slugs(values: list[str] | tuple[str, ...] | str | None) -> str:
    normalized = normalize_loyalty_category_slugs(values) or [DEFAULT_LOYALTY_CATEGORY_SLUG]
    return ",".join(normalized)


def get_loyalty_category_slugs(loyalty_settings: LoyaltySettings | None) -> list[str]:
    raw_value = getattr(loyalty_settings, "classic_category_slugs", None)
    if raw_value:
        normalized = normalize_loyalty_category_slugs(raw_value)
        if normalized:
            return normalized
    normalized = normalize_loyalty_category_slugs(getattr(loyalty_settings, "classic_category_slug", None))
    return normalized or [DEFAULT_LOYALTY_CATEGORY_SLUG]


def get_loyalty_category_slug(loyalty_settings: LoyaltySettings | None) -> str:
    return get_loyalty_category_slugs(loyalty_settings)[0]


def get_loyalty_goal(loyalty_settings: LoyaltySettings | None) -> int:
    raw_value = getattr(loyalty_settings, "paid_items_per_reward", None)
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        parsed = DEFAULT_LOYALTY_PAID_ITEMS_PER_REWARD
    return max(1, parsed)


def is_bonus_enabled(loyalty_settings: LoyaltySettings | None) -> bool:
    return bool(getattr(loyalty_settings, "bonus_enabled", True))


def is_bonus_redemption_enabled(loyalty_settings: LoyaltySettings | None) -> bool:
    return bool(getattr(loyalty_settings, "bonus_redeem_enabled", True))


def get_bonus_earn_percent(loyalty_settings: LoyaltySettings | None) -> int:
    raw_value = getattr(loyalty_settings, "bonus_earn_percent", None)
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        parsed = DEFAULT_BONUS_EARN_PERCENT
    return max(0, min(100, parsed))


def get_bonus_redeem_max_percent(loyalty_settings: LoyaltySettings | None) -> int:
    raw_value = getattr(loyalty_settings, "bonus_redeem_max_percent", None)
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        parsed = DEFAULT_BONUS_REDEEM_MAX_PERCENT
    return max(0, min(100, parsed))


def build_user_loyalty_snapshot(user: User, loyalty_settings: LoyaltySettings | None) -> tuple[int, int, int]:
    paid_count = max(0, int(user.loyalty_paid_coffee_count or 0))
    free_count = max(0, int(user.loyalty_free_coffee_count or 0))
    goal = get_loyalty_goal(loyalty_settings)
    rewards_available = max(0, paid_count // goal - free_count)
    progress = paid_count % goal
    return progress, goal, rewards_available


def is_loyalty_product(product: Product, loyalty_settings: LoyaltySettings | None) -> bool:
    target_slugs = set(get_loyalty_category_slugs(loyalty_settings))
    category_slug = product.category.slug if product.category else None
    if category_slug is not None:
        return category_slug in target_slugs
    return (product.product_type or "").strip().lower() in target_slugs


def calculate_loyalty_for_order_lines(
    order_lines: list[dict],
    user: User,
    loyalty_settings: LoyaltySettings | None,
) -> dict[str, int]:
    progress, goal, rewards_available = build_user_loyalty_snapshot(user, loyalty_settings)
    qualifying_unit_prices: list[int] = []

    for line in order_lines:
        product = line["product"]
        if not isinstance(product, Product) or not is_loyalty_product(product, loyalty_settings):
            continue

        unit_price_cents = int(line["unit_price_cents"])
        qty = int(line["qty"])
        qualifying_unit_prices.extend([unit_price_cents] * max(0, qty))

    total_qualifying_units = len(qualifying_unit_prices)
    paid_units = total_qualifying_units
    for candidate_paid_units in range(total_qualifying_units + 1):
        earned_rewards = (progress + candidate_paid_units) // goal
        available_rewards = rewards_available + earned_rewards
        candidate_free_units = total_qualifying_units - candidate_paid_units
        if candidate_free_units <= available_rewards:
            paid_units = candidate_paid_units
            break

    free_units = max(0, total_qualifying_units - paid_units)
    cheapest_prices = sorted(qualifying_unit_prices)
    loyalty_discount_cents = sum(cheapest_prices[:free_units])

    return {
        "loyalty_discount_cents": loyalty_discount_cents,
        "loyalty_paid_coffee_count": paid_units,
        "loyalty_free_coffee_count": free_units,
    }


async def get_loyalty_settings(db: AsyncSession) -> LoyaltySettings:
    loyalty_settings = await db.scalar(
        select(LoyaltySettings).where(LoyaltySettings.id == LOYALTY_SETTINGS_SINGLETON_ID)
    )
    if loyalty_settings is not None:
        return loyalty_settings

    return LoyaltySettings(
        id=LOYALTY_SETTINGS_SINGLETON_ID,
        classic_category_slug=DEFAULT_LOYALTY_CATEGORY_SLUG,
        classic_category_slugs=DEFAULT_LOYALTY_CATEGORY_SLUG,
        paid_items_per_reward=DEFAULT_LOYALTY_PAID_ITEMS_PER_REWARD,
        bonus_enabled=True,
        bonus_earn_percent=DEFAULT_BONUS_EARN_PERCENT,
        bonus_redeem_enabled=True,
        bonus_redeem_max_percent=DEFAULT_BONUS_REDEEM_MAX_PERCENT,
    )


async def get_or_create_loyalty_settings(db: AsyncSession) -> LoyaltySettings:
    loyalty_settings = await db.scalar(
        select(LoyaltySettings).where(LoyaltySettings.id == LOYALTY_SETTINGS_SINGLETON_ID)
    )
    if loyalty_settings is not None:
        return loyalty_settings

    loyalty_settings = LoyaltySettings(
        id=LOYALTY_SETTINGS_SINGLETON_ID,
        classic_category_slug=DEFAULT_LOYALTY_CATEGORY_SLUG,
        classic_category_slugs=DEFAULT_LOYALTY_CATEGORY_SLUG,
        paid_items_per_reward=DEFAULT_LOYALTY_PAID_ITEMS_PER_REWARD,
        bonus_enabled=True,
        bonus_earn_percent=DEFAULT_BONUS_EARN_PERCENT,
        bonus_redeem_enabled=True,
        bonus_redeem_max_percent=DEFAULT_BONUS_REDEEM_MAX_PERCENT,
    )
    db.add(loyalty_settings)
    await db.flush()
    return loyalty_settings
