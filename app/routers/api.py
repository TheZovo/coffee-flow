from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import Integer, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.barista_bot import send_to_baristas
from app.bot import miniapp_keyboard, send_to_user
from app.config import settings
from app.database import get_db
from app.models import Banner, BaristaShift, Category, ConsumptionPlace, Order, OrderItem, OrderStatus, OrderType, Product, PromoCode, PromoDiscountType, User
from app.schemas import BootstrapOut, CreateOrderIn, MeOut, OrderOut, ProductOut, TelegramAuthIn, UpdateProfileIn
from app.services.app_settings import get_app_settings, render_text
from app.services.barista_access import barista_now, get_active_barista_chat_ids, weekday_label
from app.services.loyalty import (
    build_user_loyalty_snapshot,
    calculate_loyalty_for_order_lines,
    get_bonus_earn_percent,
    get_bonus_redeem_max_percent,
    get_loyalty_category_slug,
    get_loyalty_category_slugs,
    get_loyalty_settings,
    is_bonus_enabled,
    is_bonus_redemption_enabled,
)
from app.services.menu import (
    build_line_name,
    minimum_size_price_cents,
    normalized_addons,
    normalized_size,
    parse_addon_options,
    resolve_size_options,
    supports_addons,
    supports_sizes,
)
from app.services.order_management import apply_order_status, today_local_date
from app.services.session_auth import sign_session_token, verify_session_token
from app.services.telegram_auth import verify_telegram_webapp_init_data
from app.services.users import get_or_create_user_by_telegram

router = APIRouter(tags=["api"])

DEFAULT_PICKUP_PRESET_MINUTES = 5


def _app_zoneinfo() -> ZoneInfo:
    try:
        return ZoneInfo(settings.APP_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _full_name(first_name: str | None, last_name: str | None) -> str | None:
    return " ".join(filter(None, [first_name, last_name])).strip() or None


def _normalize_full_name(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    if len(normalized) > 80:
        raise HTTPException(status_code=400, detail="Имя не должно быть длиннее 80 символов.")
    return normalized


def _money(cents: int) -> str:
    return f"{cents / 100:.2f} BYN"


def _setting_text(value: str | None, fallback: str) -> str:
    normalized = (value or "").strip()
    return normalized or fallback


def _order_type_label(order_type: OrderType, app_settings) -> str:
    if order_type == OrderType.DELIVERY:
        return _setting_text(app_settings.order_type_delivery_label, "Доставка")
    return _setting_text(app_settings.order_type_pickup_label, "Самовывоз")


def _status_label(status: OrderStatus, app_settings) -> str:
    labels = {
        OrderStatus.NEW: _setting_text(app_settings.order_status_new_label, "Новый"),
        OrderStatus.IN_PROGRESS: _setting_text(app_settings.order_status_in_progress_label, "В работе"),
        OrderStatus.READY: _setting_text(app_settings.order_status_ready_label, "Готов"),
        OrderStatus.EN_ROUTE: _setting_text(app_settings.order_status_en_route_label, "В пути"),
        OrderStatus.COMPLETED: _setting_text(app_settings.order_status_completed_label, "Завершен"),
        OrderStatus.CANCELLED: _setting_text(app_settings.order_status_cancelled_label, "Отменен"),
    }
    return labels.get(status, status.value)


def _consumption_place_label(consumption_place: ConsumptionPlace) -> str:
    if consumption_place == ConsumptionPlace.DINE_IN:
        return "На месте"
    return "С собой"


def _optional_money_line(label: str, cents: int) -> str:
    if not cents:
        return ""
    return f"{label}: {_money(cents)}\n"


def _optional_text_line(label: str, value: str | None) -> str:
    normalized = (value or "").strip()
    if not normalized:
        return ""
    return f"{label}: {normalized}\n"


def _with_consumption_place(text: str, consumption_place_label: str) -> str:
    normalized = (text or "").strip()
    if "Подача:" in normalized:
        return normalized
    return f"{normalized}\nПодача: {consumption_place_label}".strip()


def _build_order_template_context(order: Order, app_settings) -> dict[str, str]:
    items = getattr(order, "items", None) or []
    return {
        "order_number": order.order_number,
        "status_label": _status_label(order.status, app_settings),
        "order_type_label": _order_type_label(order.order_type, app_settings),
        "consumption_place_label": _consumption_place_label(order.consumption_place),
        "contact_name": order.contact_name or _setting_text(app_settings.order_contact_name_fallback, "Без имени"),
        "contact_phone": order.contact_phone or _setting_text(app_settings.order_contact_phone_fallback, "-"),
        "pickup_label": order.pickup_label or _setting_text(app_settings.pickup_asap_text, "Как можно скорее"),
        "items_list": "\n".join(f"• {item.name_snapshot} x{item.qty}" for item in items)
        or _setting_text(app_settings.order_empty_items_text, "• Нет позиций"),
        "total": _money(order.total_cents),
        "discount_total": _money(order.discount_cents),
        "final_total": _money(order.final_cents),
        "promo_discount": _money(order.promo_discount_cents),
        "loyalty_discount": _money(order.loyalty_discount_cents),
        "bonus_spent": _money(order.bonus_spent_cents),
        "bonus_earned": _money(order.bonus_earned_cents),
        "promo_line": _optional_money_line(
            _setting_text(app_settings.order_promo_label, "Промо"),
            order.promo_discount_cents,
        ),
        "loyalty_line": _optional_money_line(
            _setting_text(app_settings.order_loyalty_label, "Лояльность"),
            order.loyalty_discount_cents,
        ),
        "bonus_spent_line": _optional_money_line(
            _setting_text(app_settings.order_bonus_spent_label, "Списано бонусами"),
            order.bonus_spent_cents,
        ),
        "bonus_earned_line": _optional_money_line(
            _setting_text(app_settings.order_bonus_earned_label, "К начислению бонусов"),
            order.bonus_earned_cents,
        ),
        "note_line": _optional_text_line(
            _setting_text(app_settings.order_note_label, "Комментарий клиента"),
            order.note,
        ),
        "delivery_address_block": (
            f"\n{_setting_text(app_settings.order_delivery_address_label, 'Адрес')}: {order.delivery_address}"
            if order.delivery_address
            else ""
        ),
        "delivery_comment_block": (
            f"\n{_setting_text(app_settings.order_delivery_comment_label, 'Комментарий к доставке')}: {order.delivery_comment}"
            if order.delivery_comment
            else ""
        ),
    }


def _to_me_out(user: User, loyalty_settings) -> MeOut:
    loyalty_progress, loyalty_goal, loyalty_rewards_available = build_user_loyalty_snapshot(user, loyalty_settings)
    return MeOut(
        telegram_id=user.telegram_id,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        bonus_balance=user.bonus_balance,
        loyalty_category_slug=get_loyalty_category_slug(loyalty_settings),
        loyalty_category_slugs=get_loyalty_category_slugs(loyalty_settings),
        loyalty_progress=loyalty_progress,
        loyalty_goal=loyalty_goal,
        loyalty_rewards_available=loyalty_rewards_available,
        bonus_enabled=is_bonus_enabled(loyalty_settings),
        bonus_redeem_enabled=is_bonus_redemption_enabled(loyalty_settings),
        bonus_redeem_max_percent=get_bonus_redeem_max_percent(loyalty_settings),
        is_phone_verified=bool(user.phone),
    )


def _product_size_options(product: Product):
    return resolve_size_options(
        product.size_options_json,
        product_type=product.product_type,
        base_price_cents=product.price_cents,
    )


def _product_addon_options(product: Product):
    return parse_addon_options(product.addon_options_json)


def _to_product_out(product: Product) -> ProductOut:
    category_slug = product.category.slug if product.category else None
    size_options = _product_size_options(product)
    addon_options = _product_addon_options(product)
    return ProductOut(
        id=product.id,
        category_id=product.category_id,
        category_slug=category_slug,
        product_type=product.product_type,
        name=product.name,
        description=product.description,
        composition=product.composition,
        image_url=product.image_url,
        badge=product.badge,
        calories_kcal=product.calories_kcal,
        price_cents=minimum_size_price_cents(size_options, fallback=product.price_cents),
        supports_sizes=supports_sizes(size_options),
        supports_addons=supports_addons(addon_options),
        sort_order=product.sort_order,
        size_options=size_options,
        addon_options=addon_options,
    )


def _order_query():
    return select(Order).options(
        joinedload(Order.items),
        joinedload(Order.branch),
        joinedload(Order.user),
        joinedload(Order.promo_code),
    )


def _serialize_order(order: Order) -> OrderOut:
    return OrderOut.model_validate(order)


def _default_pickup_time() -> datetime:
    return datetime.now(_app_zoneinfo()) + timedelta(minutes=DEFAULT_PICKUP_PRESET_MINUTES)


def _should_secure_cookie(request: Request) -> bool:
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "").split(",", 1)[0].strip().lower()
    if forwarded_proto:
        return forwarded_proto == "https"
    if request.url.hostname in {"localhost", "127.0.0.1"}:
        return False
    return settings.PUBLIC_BASE_URL.startswith("https://")


def _resolve_pickup_choice(pickup_time_raw: str | None) -> tuple[datetime | None, str]:
    raw = (pickup_time_raw or "").strip()
    now = datetime.now(_app_zoneinfo())

    if not raw:
        target = now + timedelta(minutes=DEFAULT_PICKUP_PRESET_MINUTES)
        return target, f"Через {DEFAULT_PICKUP_PRESET_MINUTES} минут ({target.strftime('%H:%M')})"

    preset_match = re.fullmatch(r"\+(\d{1,3})", raw)
    if preset_match:
        minutes = max(1, min(240, int(preset_match.group(1))))
        target = now + timedelta(minutes=minutes)
        return target, f"Через {minutes} минут ({target.strftime('%H:%M')})"

    if re.fullmatch(r"\d{2}:\d{2}", raw):
        hours, minutes = raw.split(":", 1)
        target_time = time(hour=int(hours), minute=int(minutes))
        target = datetime.combine(now.date(), target_time).replace(tzinfo=now.tzinfo)
        min_allowed = now + timedelta(minutes=5)
        if target >= min_allowed:
            return target, raw

    return None, raw[:80]


def _calculate_bonus_cap_cents(
    *,
    gross_total: int,
    promo_discount_cents: int,
    loyalty_discount_cents: int,
    user_bonus_balance: int,
    loyalty_settings,
) -> int:
    if not is_bonus_redemption_enabled(loyalty_settings):
        return 0
    remaining_after_discounts = max(0, gross_total - promo_discount_cents - loyalty_discount_cents)
    percent_limit = remaining_after_discounts * get_bonus_redeem_max_percent(loyalty_settings) // 100
    return min(max(0, user_bonus_balance), remaining_after_discounts, percent_limit)


def _bonus_limit_error_message(max_bonus_spend: int, loyalty_settings) -> str:
    percent = get_bonus_redeem_max_percent(loyalty_settings)
    return (
        f"Нельзя использовать бонусов больше, чем {percent}% от заказа. "
        f"Сейчас максимум: {_money(max_bonus_spend)}."
    )


def _bonus_limit_error_message(
    *,
    requested_bonus_cents: int,
    user_bonus_balance: int,
    max_bonus_spend: int,
    loyalty_settings,
) -> str:
    if requested_bonus_cents > max(0, user_bonus_balance):
        return f"Нельзя списать больше бонусов, чем у вас есть. Сейчас на счёте: {_money(user_bonus_balance)}."
    percent = get_bonus_redeem_max_percent(loyalty_settings)
    return f"Нельзя использовать бонусов больше, чем {percent}% от заказа. Сейчас максимум: {_money(max_bonus_spend)}."


def _shift_starts_at(current: datetime, shift: BaristaShift) -> datetime:
    days_ahead = (int(shift.weekday) - current.weekday()) % 7
    candidate_day = current.date() + timedelta(days=days_ahead)
    candidate = datetime.combine(candidate_day, shift.start_time, tzinfo=current.tzinfo)
    if candidate <= current:
        candidate += timedelta(days=7)
    return candidate


async def _nearest_barista_shift_label(db: AsyncSession) -> str | None:
    shifts = (
        await db.execute(
            select(BaristaShift)
            .where(BaristaShift.is_active.is_(True))
            .order_by(BaristaShift.weekday.asc(), BaristaShift.start_time.asc(), BaristaShift.id.asc())
        )
    ).scalars().all()
    if not shifts:
        return None
    current = barista_now()
    next_shift = min(shifts, key=lambda shift: (_shift_starts_at(current, shift), shift.id))
    return f"{weekday_label(next_shift.weekday)} {next_shift.start_time.strftime('%H:%M')}"


async def _get_user_from_session_cookie(request: Request, db: AsyncSession) -> User | None:
    token = request.cookies.get("coffee_session", "")
    payload = verify_session_token(token=token, secret=settings.SESSION_SECRET)
    if payload is None:
        return None

    result = await db.execute(select(User).where(User.telegram_id == int(payload["tg"])))
    return result.scalar_one_or_none()


async def _resolve_identity_from_request(request: Request) -> tuple[int, str | None, str | None] | None:
    init_data = request.headers.get("X-Telegram-Init-Data", "").strip()
    if init_data:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise HTTPException(status_code=500, detail="Не настроен TELEGRAM_BOT_TOKEN.")
        tg_user = verify_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=settings.TELEGRAM_BOT_TOKEN,
            ttl_seconds=settings.INITDATA_TTL_SECONDS,
        )
        return (
            int(tg_user["id"]),
            tg_user.get("username"),
            _full_name(tg_user.get("first_name"), tg_user.get("last_name")),
        )

    if settings.DEBUG_ALLOW_FAKE_INITDATA:
        debug_id = request.headers.get("X-Debug-Telegram-Id", "").strip()
        if debug_id:
            try:
                telegram_id = int(debug_id)
            except ValueError as exc:
                raise HTTPException(status_code=401, detail="Некорректный debug Telegram ID.") from exc
            return (
                telegram_id,
                request.headers.get("X-Debug-Username"),
                request.headers.get("X-Debug-Full-Name"),
            )

    return None


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    cookie_user = await _get_user_from_session_cookie(request=request, db=db)
    if cookie_user is not None:
        return cookie_user

    identity = await _resolve_identity_from_request(request)
    if identity is None:
        raise HTTPException(status_code=401, detail="Сессия не найдена. Откройте Mini App из Telegram-бота.")

    telegram_id, username, full_name = identity
    user = await get_or_create_user_by_telegram(
        session=db,
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
    )
    await db.commit()
    await db.refresh(user)
    return user


async def _generate_order_number(db: AsyncSession, order_day: date) -> str:
    advisory_key = int(order_day.strftime("%Y%m%d"))
    await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": advisory_key})
    last_number = await db.scalar(
        select(func.max(cast(Order.order_number, Integer))).where(Order.order_day == order_day)
    )
    return str((last_number or 0) + 1)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/auth/telegram", response_model=MeOut)
async def auth_telegram(
    payload: TelegramAuthIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MeOut:
    loyalty_settings = await get_loyalty_settings(db)
    active_barista_chat_ids = await get_active_barista_chat_ids(db)
    if not active_barista_chat_ids:
        next_shift_label = await _nearest_barista_shift_label(db)
        detail = "Сейчас бариста не на смене. Пожалуйста, оформите заказ в рабочее время."
        if next_shift_label:
            detail = f"{detail} Ближайшая смена: {next_shift_label}."
        raise HTTPException(status_code=400, detail=detail)
    existing_user = await _get_user_from_session_cookie(request=request, db=db)
    if existing_user is not None:
        return _to_me_out(existing_user, loyalty_settings)

    init_data = (payload.init_data or "").strip()
    if init_data:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise HTTPException(status_code=500, detail="Не настроен TELEGRAM_BOT_TOKEN.")
        tg_user = verify_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=settings.TELEGRAM_BOT_TOKEN,
            ttl_seconds=settings.INITDATA_TTL_SECONDS,
        )
        telegram_id = int(tg_user["id"])
        username = tg_user.get("username")
        full_name = _full_name(tg_user.get("first_name"), tg_user.get("last_name"))
    else:
        identity = await _resolve_identity_from_request(request)
        if identity is None:
            raise HTTPException(status_code=401, detail="Не удалось подтвердить пользователя Telegram.")
        telegram_id, username, full_name = identity

    user = await get_or_create_user_by_telegram(
        session=db,
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
    )
    await db.commit()
    await db.refresh(user)

    token = sign_session_token(
        telegram_id=user.telegram_id,
        secret=settings.SESSION_SECRET,
        ttl_seconds=settings.SESSION_TTL_SECONDS,
    )
    response.set_cookie(
        key="coffee_session",
        value=token,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=_should_secure_cookie(request),
        path="/",
    )
    return _to_me_out(user, loyalty_settings)


@router.get("/api/bootstrap", response_model=BootstrapOut)
async def bootstrap(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BootstrapOut:
    loyalty_settings = await get_loyalty_settings(db)
    banners = (
        await db.execute(
            select(Banner).where(Banner.is_active.is_(True)).order_by(Banner.sort_order.asc(), Banner.id.asc())
        )
    ).scalars().all()
    categories = (
        await db.execute(
            select(Category).where(Category.is_active.is_(True)).order_by(Category.sort_order.asc(), Category.id.asc())
        )
    ).scalars().all()
    products = (
        await db.execute(
            select(Product)
            .options(joinedload(Product.category))
            .outerjoin(Product.category)
            .where(Product.is_active.is_(True))
            .where((Product.category_id.is_(None)) | (Category.is_active.is_(True)))
            .order_by(Product.category_id.asc().nulls_last(), Product.sort_order.asc(), Product.id.asc())
        )
    ).scalars().all()

    return BootstrapOut(
        me=_to_me_out(user, loyalty_settings),
        banners=banners,
        categories=categories,
        products=[_to_product_out(product) for product in products],
    )


@router.get("/api/me", response_model=MeOut)
async def me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeOut:
    loyalty_settings = await get_loyalty_settings(db)
    return _to_me_out(user, loyalty_settings)


@router.put("/api/me/profile", response_model=MeOut)
async def update_profile(
    payload: UpdateProfileIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeOut:
    loyalty_settings = await get_loyalty_settings(db)
    if "full_name" in payload.model_fields_set:
        user.full_name = _normalize_full_name(payload.full_name)

    await db.commit()
    await db.refresh(user)
    return _to_me_out(user, loyalty_settings)


@router.post("/api/orders", response_model=OrderOut)
async def create_order(
    payload: CreateOrderIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    loyalty_settings = await get_loyalty_settings(db)
    if not user.phone:
        raise HTTPException(status_code=400, detail="Разрешите приложению получить телефон из Telegram.")
    if not user.full_name:
        raise HTTPException(status_code=400, detail="Перед заказом укажите имя в профиле.")
    if not payload.items:
        raise HTTPException(status_code=400, detail="Корзина пустая.")
    if payload.order_type != OrderType.PICKUP:
        raise HTTPException(status_code=400, detail="Сейчас доступен только самовывоз.")

    product_ids = sorted({item.product_id for item in payload.items})
    products = (
        await db.execute(
            select(Product)
            .options(joinedload(Product.category))
            .outerjoin(Product.category)
            .where(Product.id.in_(product_ids), Product.is_active.is_(True))
            .where((Product.category_id.is_(None)) | (Category.is_active.is_(True)))
        )
    ).scalars().all()
    products_by_id = {product.id: product for product in products}
    if len(products_by_id) != len(product_ids):
        raise HTTPException(status_code=400, detail="Некоторые позиции уже недоступны.")

    subtotal_cents = 0
    order_lines: list[dict] = []
    for item in payload.items:
        product = products_by_id.get(item.product_id)
        if product is None:
            raise HTTPException(status_code=400, detail="Некоторые позиции уже недоступны.")

        size_options = _product_size_options(product)
        addon_options = _product_addon_options(product)
        size = normalized_size(item.size_code, size_options)
        addons = normalized_addons(item.addon_codes, addon_options)
        addons_total = sum(addon.price_cents for addon in addons)
        unit_price_cents = (size.price_cents if size is not None else product.price_cents) + addons_total
        subtotal_cents += unit_price_cents * item.qty
        order_lines.append(
            {
                "product": product,
                "qty": item.qty,
                "unit_price_cents": unit_price_cents,
                "name_snapshot": build_line_name(product.name, size, addons),
            }
        )

    gross_total = subtotal_cents

    promo: PromoCode | None = None
    promo_discount_cents = 0
    promo_code_value = (payload.promo_code or "").strip().upper()
    if promo_code_value:
        promo = await db.scalar(
            select(PromoCode).where(PromoCode.code == promo_code_value, PromoCode.is_active.is_(True))
        )
        if promo is None:
            raise HTTPException(status_code=400, detail="Промокод не найден.")
        now_utc = datetime.now(timezone.utc)
        if promo.expires_at and promo.expires_at < now_utc:
            raise HTTPException(status_code=400, detail="Срок действия промокода истек.")
        if promo.max_uses is not None and promo.used_count >= promo.max_uses:
            raise HTTPException(status_code=400, detail="Лимит применений промокода исчерпан.")

        if promo.discount_type == PromoDiscountType.PERCENT:
            promo_discount_cents = gross_total * max(0, min(promo.discount_value, 100)) // 100
        else:
            promo_discount_cents = min(gross_total, max(0, promo.discount_value))

    loyalty_result = calculate_loyalty_for_order_lines(order_lines, user, loyalty_settings)
    loyalty_discount_cents = min(
        loyalty_result["loyalty_discount_cents"],
        max(0, gross_total - promo_discount_cents),
    )
    max_bonus_spend = _calculate_bonus_cap_cents(
        gross_total=gross_total,
        promo_discount_cents=promo_discount_cents,
        loyalty_discount_cents=loyalty_discount_cents,
        user_bonus_balance=user.bonus_balance,
        loyalty_settings=loyalty_settings,
    )
    bonus_spent_cents = 0
    if is_bonus_redemption_enabled(loyalty_settings):
        requested_bonus_cents = max(0, int(payload.use_bonus_cents or 0))
        if requested_bonus_cents > max_bonus_spend:
            raise HTTPException(
                status_code=400,
                detail=_bonus_limit_error_message(
                    requested_bonus_cents=requested_bonus_cents,
                    user_bonus_balance=user.bonus_balance,
                    max_bonus_spend=max_bonus_spend,
                    loyalty_settings=loyalty_settings,
                ),
            )
        if requested_bonus_cents > max_bonus_spend:
            raise HTTPException(
                status_code=400,
                detail=_bonus_limit_error_message(max_bonus_spend, loyalty_settings),
            )
        if requested_bonus_cents > max_bonus_spend:
            raise HTTPException(
                status_code=400,
                detail="Сумма списания бонусов превышает доступный лимит для этого заказа.",
            )
        bonus_spent_cents = requested_bonus_cents
    elif payload.use_bonus_cents:
        raise HTTPException(status_code=400, detail="Списание бонусов сейчас отключено.")

    total_discount_cents = min(gross_total, promo_discount_cents + loyalty_discount_cents + bonus_spent_cents)
    final_cents = max(0, gross_total - total_discount_cents)
    bonus_earned_cents = 0
    if is_bonus_enabled(loyalty_settings):
        bonus_earned_cents = final_cents * get_bonus_earn_percent(loyalty_settings) // 100

    order_day = today_local_date()
    pickup_at, pickup_label = _resolve_pickup_choice(payload.pickup_time)
    order = Order(
        order_day=order_day,
        order_number=await _generate_order_number(db, order_day),
        user_id=user.id,
        branch_id=None,
        promo_code_id=promo.id if promo else None,
        order_type=OrderType.PICKUP,
        consumption_place=payload.consumption_place,
        contact_name=user.full_name,
        contact_phone=user.phone,
        scheduled_for=pickup_at,
        pickup_label=pickup_label,
        total_cents=gross_total,
        discount_cents=total_discount_cents,
        final_cents=final_cents,
        delivery_fee_cents=0,
        promo_discount_cents=promo_discount_cents,
        bonus_spent_cents=bonus_spent_cents,
        bonus_earned_cents=bonus_earned_cents,
        loyalty_discount_cents=loyalty_discount_cents,
        loyalty_paid_coffee_count=loyalty_result["loyalty_paid_coffee_count"],
        loyalty_free_coffee_count=loyalty_result["loyalty_free_coffee_count"],
        loyalty_reserved=False,
        note=(payload.note or "").strip() or None,
        pickup_eta_minutes=settings.DEFAULT_PICKUP_ETA_MINUTES,
    )
    db.add(order)
    await db.flush()

    for line in order_lines:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=line["product"].id,
                qty=line["qty"],
                price_cents=line["unit_price_cents"],
                name_snapshot=line["name_snapshot"],
            )
        )

    if promo is not None:
        promo.used_count += 1
    if bonus_spent_cents:
        user.bonus_balance -= bonus_spent_cents

    await db.commit()

    created_order = (
        await db.execute(_order_query().where(Order.id == order.id))
    ).unique().scalar_one()
    app_settings = await get_app_settings(db)
    order_context = _build_order_template_context(created_order, app_settings)

    await send_to_baristas(
        _with_consumption_place(
            render_text(app_settings.barista_new_order_text, **order_context),
            order_context["consumption_place_label"],
        ),
        order_id=created_order.id,
    )
    if created_order.user is not None:
        await send_to_user(
            created_order.user.telegram_id,
            render_text(app_settings.customer_order_created_text, **order_context),
            reply_markup=miniapp_keyboard(app_settings.miniapp_button_text),
        )
    return _serialize_order(created_order)


@router.get("/api/orders/me", response_model=list[OrderOut])
async def my_orders(
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OrderOut]:
    result = await db.execute(
        _order_query()
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    orders = result.unique().scalars().all()
    return [_serialize_order(order) for order in orders]


@router.post("/api/orders/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    result = await db.execute(
        _order_query()
        .where(Order.id == order_id, Order.user_id == user.id)
        .limit(1)
    )
    order = result.unique().scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден.")
    if order.status not in {OrderStatus.NEW, OrderStatus.IN_PROGRESS}:
        raise HTTPException(status_code=409, detail="Этот заказ уже нельзя отменить.")

    updated_order = await apply_order_status(db, order, OrderStatus.CANCELLED)
    refreshed_order = (
        await db.execute(_order_query().where(Order.id == updated_order.id))
    ).unique().scalar_one()
    app_settings = await get_app_settings(db)
    order_context = _build_order_template_context(refreshed_order, app_settings)
    await send_to_baristas(
        render_text(
            "⚠️ Клиент отменил заказ №{order_number}\n"
            "Формат: {order_type_label}\n"
            "Подача: {consumption_place_label}\n"
            "Клиент: {contact_name}\n"
            "Телефон: {contact_phone}",
            **order_context,
        ),
        order_id=refreshed_order.id,
    )
    return _serialize_order(refreshed_order)
