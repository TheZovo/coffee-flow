from __future__ import annotations

from datetime import date, datetime, time, timedelta
import re
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.database import get_db
from app.models import Banner, BaristaShift, Category, Product, User
from app.schemas import (
    AdminAppSettingsIn,
    AdminAppSettingsOut,
    AdminAnalyticsOut,
    AdminBannerIn,
    AdminBannerOut,
    AdminBaristaIn,
    AdminBaristaOut,
    AdminBaristaShiftIn,
    AdminBaristaShiftOut,
    AdminBootstrapOut,
    AdminCategoryIn,
    AdminCategoryOut,
    AdminLoginIn,
    AdminProgramsSettingsIn,
    AdminProgramsSettingsOut,
    AdminProductIn,
    AdminProductOut,
    AdminReminderSettingsIn,
    AdminReminderSettingsOut,
    AdminUploadOut,
)
from app.services.analytics import build_analytics, build_analytics_csv_bytes, build_analytics_xlsx_bytes, default_period
from app.services.app_settings import APP_SETTINGS_FIELDS, get_app_settings, get_or_create_app_settings
from app.services.barista_access import is_placeholder_telegram_id, normalize_barista_username, weekday_label
from app.services.loyalty import (
    get_bonus_earn_percent,
    get_bonus_redeem_max_percent,
    get_loyalty_category_slug,
    get_loyalty_category_slugs,
    get_loyalty_goal,
    get_loyalty_settings,
    get_or_create_loyalty_settings,
    is_bonus_enabled,
    is_bonus_redemption_enabled,
    normalize_loyalty_category_slugs,
    serialize_loyalty_category_slugs,
)
from app.services.menu import (
    minimum_size_price_cents,
    normalize_addon_options,
    normalize_size_options,
    parse_addon_options,
    resolve_size_options,
    serialize_option_payloads,
    supports_addons,
    supports_sizes,
)
from app.services.session_auth import sign_role_session_token, verify_role_session_token

router = APIRouter(tags=["admin"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
UPLOADS_DIR = BASE_DIR / "static" / "uploads"

ADMIN_COOKIE_NAME = "coffee_admin_session"
ADMIN_ROLE = "barista_admin"
MAX_IMAGE_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".gif": "image/gif",
}


def _admin_session_secret() -> str:
    return f"{settings.SESSION_SECRET}:{settings.BARISTA_SECRET}:admin"


def _should_secure_cookie(request: Request) -> bool:
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "").split(",", 1)[0].strip().lower()
    if forwarded_proto:
        return forwarded_proto == "https"
    if request.url.hostname in {"localhost", "127.0.0.1"}:
        return False
    return settings.PUBLIC_BASE_URL.startswith("https://")


def _trimmed(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _normalize_category_slug(value: str) -> str:
    slug = value.strip().lower().replace("_", "-")
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^\w-]+", "", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        raise HTTPException(status_code=400, detail="Укажите корректный slug категории.")
    if len(slug) > 80:
        raise HTTPException(status_code=400, detail="Slug категории не должен быть длиннее 80 символов.")
    return slug


def _normalize_category_name(value: str) -> str:
    name = _trimmed(value)
    if not name:
        raise HTTPException(status_code=400, detail="Укажите название категории.")
    if len(name) > 120:
        raise HTTPException(status_code=400, detail="Название категории не должно быть длиннее 120 символов.")
    return name


def _normalize_username(value: str | None) -> str | None:
    normalized = _trimmed(value)
    if not normalized:
        return None
    return normalized.lstrip("@")


def _normalize_barista_name(value: str) -> str:
    name = _trimmed(value)
    if not name:
        raise HTTPException(status_code=400, detail="Укажите имя бариста.")
    if len(name) > 255:
        raise HTTPException(status_code=400, detail="Имя бариста не должно быть длиннее 255 символов.")
    return name


def _normalize_barista_payload(payload: AdminBaristaIn) -> dict[str, str | int | bool | None]:
    telegram_id = int(payload.telegram_id) if payload.telegram_id else None
    return {
        "telegram_id": telegram_id,
        "username": normalize_barista_username(payload.username),
        "full_name": _normalize_barista_name(payload.full_name),
        "is_barista": bool(payload.is_barista),
    }


def _display_barista_telegram_id(telegram_id: int | None) -> int | None:
    if is_placeholder_telegram_id(telegram_id):
        return None
    return telegram_id


def _normalize_banner_payload(payload: AdminBannerIn) -> dict:
    title = _trimmed(payload.title)
    if not title:
        raise HTTPException(status_code=400, detail="Укажите заголовок баннера.")

    return {
        "title": title,
        "subtitle": _trimmed(payload.subtitle),
        "description": _trimmed(payload.description),
        "image_url": _trimmed(payload.image_url),
        "sort_order": payload.sort_order,
        "is_active": payload.is_active,
    }


def _normalize_product_payload(payload: AdminProductIn) -> dict:
    product_type = _trimmed(payload.product_type)
    if not product_type:
        raise HTTPException(status_code=400, detail="Укажите тип продукции.")

    name = _trimmed(payload.name)
    if not name:
        raise HTTPException(status_code=400, detail="Укажите название товара.")

    size_options = normalize_size_options([item.model_dump() for item in payload.size_options])
    addon_options = normalize_addon_options([item.model_dump() for item in payload.addon_options])
    if not size_options:
        raise HTTPException(status_code=400, detail="Добавьте хотя бы один размер с ценой.")

    min_price_cents = minimum_size_price_cents(
        resolve_size_options(size_options, product_type=product_type, base_price_cents=0),
        fallback=0,
    )

    return {
        "category_id": payload.category_id,
        "product_type": product_type,
        "name": name,
        "description": _trimmed(payload.description),
        "composition": _trimmed(payload.composition),
        "image_url": _trimmed(payload.image_url),
        "badge": _trimmed(payload.badge),
        "volume_ml": None,
        "weight_g": None,
        "calories_kcal": payload.calories_kcal,
        "price_cents": min_price_cents,
        "sort_order": payload.sort_order,
        "has_sizes": supports_sizes(resolve_size_options(size_options, product_type=product_type, base_price_cents=0)),
        "has_addons": supports_addons(parse_addon_options(addon_options)),
        "size_options_json": serialize_option_payloads(size_options),
        "addon_options_json": serialize_option_payloads(addon_options),
        "is_active": payload.is_active,
    }


def _serialize_product(product: Product) -> AdminProductOut:
    category_slug = product.category.slug if product.category else None
    category_name = product.category.name if product.category else None
    size_options = resolve_size_options(
        product.size_options_json,
        product_type=product.product_type,
        base_price_cents=product.price_cents,
    )
    addon_options = parse_addon_options(product.addon_options_json)
    return AdminProductOut(
        id=product.id,
        category_id=product.category_id,
        category_slug=category_slug,
        category_name=category_name,
        product_type=product.product_type,
        name=product.name,
        description=product.description,
        composition=product.composition,
        image_url=product.image_url,
        badge=product.badge,
        calories_kcal=product.calories_kcal,
        price_cents=minimum_size_price_cents(size_options, fallback=product.price_cents),
        sort_order=product.sort_order,
        has_sizes=supports_sizes(size_options),
        has_addons=supports_addons(addon_options),
        is_active=product.is_active,
        size_options=size_options,
        addon_options=addon_options,
    )


def _serialize_banner(banner: Banner) -> AdminBannerOut:
    return AdminBannerOut.model_validate(banner)


def _serialize_barista(user: User) -> AdminBaristaOut:
    return AdminBaristaOut(
        id=user.id,
        telegram_id=_display_barista_telegram_id(user.telegram_id),
        username=user.username,
        full_name=user.full_name,
        is_barista=user.is_barista,
        is_pending=is_placeholder_telegram_id(user.telegram_id),
        created_at=user.created_at,
    )


def _serialize_barista_shift(shift: BaristaShift) -> AdminBaristaShiftOut:
    display_name = (
        (shift.user.full_name or "").strip()
        or (shift.user.username or "").strip()
        or f"Бариста #{shift.user_id}"
    )
    return AdminBaristaShiftOut(
        id=shift.id,
        user_id=shift.user_id,
        barista_name=display_name,
        barista_username=shift.user.username,
        barista_telegram_id=_display_barista_telegram_id(shift.user.telegram_id),
        barista_is_pending=is_placeholder_telegram_id(shift.user.telegram_id),
        weekday=shift.weekday,
        start_time=shift.start_time,
        end_time=shift.end_time,
        note=shift.note,
        is_active=shift.is_active,
        created_at=shift.created_at,
    )


def _serialize_program_settings(loyalty_settings) -> AdminProgramsSettingsOut:
    loyalty_category_slugs = get_loyalty_category_slugs(loyalty_settings)
    return AdminProgramsSettingsOut(
        classic_category_slug=loyalty_category_slugs[0],
        classic_category_slugs=loyalty_category_slugs,
        paid_items_per_reward=get_loyalty_goal(loyalty_settings),
        bonus_enabled=is_bonus_enabled(loyalty_settings),
        bonus_earn_percent=get_bonus_earn_percent(loyalty_settings),
        bonus_redeem_enabled=is_bonus_redemption_enabled(loyalty_settings),
        bonus_redeem_max_percent=get_bonus_redeem_max_percent(loyalty_settings),
    )


def _serialize_app_settings(app_settings) -> AdminAppSettingsOut:
    return AdminAppSettingsOut(
        **{
            field_name: str(getattr(app_settings, field_name, "") or "")
            for field_name in APP_SETTINGS_FIELDS
        }
    )


def _serialize_reminder_settings(app_settings) -> AdminReminderSettingsOut:
    return AdminReminderSettingsOut(
        inactive_reminder_enabled=bool(getattr(app_settings, "inactive_reminder_enabled", False)),
        inactive_reminder_days=max(1, int(getattr(app_settings, "inactive_reminder_days", 30) or 30)),
        inactive_reminder_send_time=str(getattr(app_settings, "inactive_reminder_send_time", "12:00") or "12:00"),
        inactive_reminder_text=str(getattr(app_settings, "inactive_reminder_text", "") or ""),
        inactive_reminder_last_run_at=getattr(app_settings, "inactive_reminder_last_run_at", None),
    )


async def _normalize_program_settings_payload(
    payload: AdminProgramsSettingsIn,
    db: AsyncSession,
) -> dict[str, int | str | bool]:
    requested_category_slugs = payload.classic_category_slugs or [payload.classic_category_slug or ""]
    classic_category_slugs = normalize_loyalty_category_slugs(requested_category_slugs)
    if not classic_category_slugs:
        raise HTTPException(status_code=400, detail="Укажите категорию для программы лояльности.")

    existing_category_slugs = set(
        (
            await db.execute(
                select(Category.slug).where(Category.slug.in_(classic_category_slugs))
            )
        ).scalars().all()
    )
    missing_category_slugs = [slug for slug in classic_category_slugs if slug not in existing_category_slugs]
    if missing_category_slugs:
        missing_label = ", ".join(missing_category_slugs)
        raise HTTPException(
            status_code=404,
            detail=f"Категории для программы лояльности не найдены: {missing_label}.",
        )

    return {
        "classic_category_slug": classic_category_slugs[0],
        "classic_category_slugs": serialize_loyalty_category_slugs(classic_category_slugs),
        "paid_items_per_reward": payload.paid_items_per_reward,
        "bonus_enabled": payload.bonus_enabled,
        "bonus_earn_percent": payload.bonus_earn_percent,
        "bonus_redeem_enabled": payload.bonus_redeem_enabled,
        "bonus_redeem_max_percent": payload.bonus_redeem_max_percent,
    }


def _normalize_reminder_settings_payload(payload: AdminReminderSettingsIn) -> dict[str, object]:
    send_time = (payload.inactive_reminder_send_time or "").strip()
    if not re.fullmatch(r"\d{2}:\d{2}", send_time):
        raise HTTPException(status_code=400, detail="Время отправки напоминания укажите в формате HH:MM.")
    hours, minutes = send_time.split(":", 1)
    if int(hours) > 23 or int(minutes) > 59:
        raise HTTPException(status_code=400, detail="Время отправки напоминания указано некорректно.")
    return {
        "inactive_reminder_enabled": bool(payload.inactive_reminder_enabled),
        "inactive_reminder_days": int(payload.inactive_reminder_days),
        "inactive_reminder_send_time": send_time,
        "inactive_reminder_text": (payload.inactive_reminder_text or "").strip(),
    }


def _resolve_report_period(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    resolved_from, resolved_to = default_period()
    if date_from is not None:
        resolved_from = date_from
    if date_to is not None:
        resolved_to = date_to
    if resolved_from > resolved_to:
        raise HTTPException(status_code=400, detail="Дата начала периода не может быть позже даты окончания.")
    return resolved_from, resolved_to


async def _normalize_barista_shift_payload(
    payload: AdminBaristaShiftIn,
    db: AsyncSession,
    exclude_shift_id: int | None = None,
) -> dict[str, time | int | bool | str | None]:
    user = await db.get(User, payload.user_id)
    if user is None or not user.is_barista:
        raise HTTPException(status_code=404, detail="Бариста для смены не найден.")

    starts_at = _normalize_shift_boundary(payload.starts_at)
    ends_at = _normalize_shift_boundary(payload.ends_at)
    if ends_at <= starts_at:
        raise HTTPException(status_code=400, detail="Конец смены должен быть позже начала.")

    if payload.is_active:
        overlapping_shift = await db.scalar(
            select(BaristaShift).where(
                BaristaShift.user_id == payload.user_id,
                BaristaShift.id != (exclude_shift_id or 0),
                BaristaShift.is_active.is_(True),
                BaristaShift.starts_at < ends_at,
                BaristaShift.ends_at > starts_at,
            )
        )
        if overlapping_shift is not None:
            raise HTTPException(
                status_code=409,
                detail="У этого бариста уже есть пересекающаяся активная смена.",
            )

    return {
        "user_id": payload.user_id,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "note": _trimmed(payload.note),
        "is_active": bool(payload.is_active),
    }


def _barista_zoneinfo() -> ZoneInfo:
    try:
        return ZoneInfo(settings.APP_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _materialize_shift_window(weekday: int, start_time: time, end_time: time) -> tuple[datetime, datetime]:
    now = datetime.now(_barista_zoneinfo())
    days_ahead = (int(weekday) - now.weekday()) % 7
    target_day = now.date() + timedelta(days=days_ahead)
    starts_at = datetime.combine(target_day, start_time, tzinfo=now.tzinfo)
    ends_at = datetime.combine(target_day, end_time, tzinfo=now.tzinfo)
    if ends_at <= starts_at:
        ends_at = starts_at + timedelta(minutes=1)
    return starts_at, ends_at


async def _normalize_barista_shift_payload(
    payload: AdminBaristaShiftIn,
    db: AsyncSession,
    exclude_shift_id: int | None = None,
) -> dict[str, time | int | bool | str | None]:
    del exclude_shift_id
    user = await db.get(User, payload.user_id)
    if user is None or not user.is_barista:
        raise HTTPException(status_code=404, detail="Бариста для смены не найден.")

    start_time = payload.start_time
    end_time = payload.end_time
    starts_at = None
    ends_at = None
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="Конец смены должен быть позже начала.")

    starts_at, ends_at = _materialize_shift_window(int(payload.weekday), start_time, end_time)

    return {
        "user_id": payload.user_id,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "weekday": int(payload.weekday),
        "start_time": start_time,
        "end_time": end_time,
        "note": _trimmed(payload.note),
        "is_active": bool(payload.is_active),
    }


def _resolve_upload_extension(filename: str | None, content_type: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        return suffix

    normalized_content_type = (content_type or "").lower().strip()
    for extension, allowed_content_type in ALLOWED_IMAGE_EXTENSIONS.items():
        if normalized_content_type == allowed_content_type:
            return extension

    raise HTTPException(
        status_code=400,
        detail="Поддерживаются только PNG, JPG, WEBP, SVG и GIF.",
    )


async def require_admin(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    token = request.cookies.get(ADMIN_COOKIE_NAME, "")
    if verify_role_session_token(token=token, secret=_admin_session_secret(), expected_role=ADMIN_ROLE) is None:
        raise HTTPException(status_code=401, detail="Требуется вход в админ-панель.")
    return None


async def _get_category_or_none(category_id: int | None, db: AsyncSession) -> Category | None:
    if category_id is None:
        return None
    category = await db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Категория не найдена.")
    return category


async def _get_banner_or_404(banner_id: int, db: AsyncSession) -> Banner:
    banner = await db.get(Banner, banner_id)
    if banner is None:
        raise HTTPException(status_code=404, detail="Баннер не найден.")
    return banner


async def _get_product_or_404(product_id: int, db: AsyncSession) -> Product:
    result = await db.execute(
        select(Product)
        .options(joinedload(Product.category))
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден.")
    return product


async def _get_barista_or_404(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(
        select(User)
        .options(joinedload(User.barista_shifts))
        .where(User.id == user_id)
    )
    user = result.unique().scalar_one_or_none()
    if user is None or (not user.is_barista and not user.barista_shifts):
        raise HTTPException(status_code=404, detail="Бариста не найден.")
    return user


async def _get_barista_shift_or_404(shift_id: int, db: AsyncSession) -> BaristaShift:
    result = await db.execute(
        select(BaristaShift)
        .options(joinedload(BaristaShift.user))
        .where(BaristaShift.id == shift_id)
    )
    shift = result.scalar_one_or_none()
    if shift is None:
        raise HTTPException(status_code=404, detail="Смена не найдена.")
    return shift


async def _find_unique_user_by_username(username: str | None, db: AsyncSession) -> User | None:
    if not username:
        return None

    result = await db.execute(
        select(User)
        .where(
            func.lower(User.username) == username,
            User.telegram_id < 0,
        )
        .order_by(User.id.asc())
    )
    users = result.scalars().all()
    if not users:
        return None
    if len(users) > 1:
        raise HTTPException(
            status_code=409,
            detail="Найдено несколько пользователей с таким username. Уточните запись через первый вход бариста в бот.",
        )
    return users[0]


async def _find_unique_pending_barista_by_name(full_name: str | None, db: AsyncSession) -> User | None:
    if not full_name:
        return None

    result = await db.execute(
        select(User)
        .where(
            User.is_barista.is_(True),
            User.telegram_id < 0,
            or_(User.username.is_(None), User.username == ""),
            func.lower(User.full_name) == full_name.lower(),
        )
        .order_by(User.id.asc())
    )
    users = result.scalars().all()
    if not users:
        return None
    if len(users) > 1:
        raise HTTPException(
            status_code=409,
            detail="Найдено несколько ожидающих записей бариста с таким именем. Уточните username или удалите дубликат.",
        )
    return users[0]


async def _reserve_placeholder_telegram_id(db: AsyncSession) -> int:
    smallest_existing = await db.scalar(
        select(User.telegram_id)
        .where(User.telegram_id < 0)
        .order_by(User.telegram_id.asc())
        .limit(1)
    )
    return int(smallest_existing - 1) if smallest_existing is not None else -1


@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={},
    )


@router.post("/api/admin/login")
async def admin_login(payload: AdminLoginIn, request: Request, response: Response) -> dict[str, bool]:
    if payload.secret.strip() != settings.BARISTA_SECRET:
        raise HTTPException(status_code=401, detail="Неверный секрет админ-панели.")

    token = sign_role_session_token(
        role=ADMIN_ROLE,
        secret=_admin_session_secret(),
        ttl_seconds=settings.SESSION_TTL_SECONDS,
    )
    response.set_cookie(
        key=ADMIN_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=_should_secure_cookie(request),
        path="/",
    )
    return {"ok": True}


@router.post("/api/admin/logout")
async def admin_logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(key=ADMIN_COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/api/admin/bootstrap", response_model=AdminBootstrapOut)
async def admin_bootstrap(
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBootstrapOut:
    program_settings = await get_loyalty_settings(db)
    app_settings = await get_app_settings(db)
    banners = (
        await db.execute(
            select(Banner).order_by(Banner.sort_order.asc(), Banner.id.asc())
        )
    ).scalars().all()
    categories = (
        await db.execute(
            select(Category).order_by(Category.sort_order.asc(), Category.id.asc())
        )
    ).scalars().all()
    products = (
        await db.execute(
            select(Product)
            .options(joinedload(Product.category))
            .order_by(Product.category_id.asc().nulls_last(), Product.sort_order.asc(), Product.id.asc())
        )
    ).scalars().all()
    baristas = (
        await db.execute(
            select(User)
            .outerjoin(BaristaShift, BaristaShift.user_id == User.id)
            .where(or_(User.is_barista.is_(True), BaristaShift.id.is_not(None)))
            .order_by(User.full_name.asc().nulls_last(), User.id.asc())
            .distinct()
        )
    ).scalars().all()
    barista_shifts = (
        await db.execute(
            select(BaristaShift)
            .options(joinedload(BaristaShift.user))
            .order_by(BaristaShift.weekday.asc(), BaristaShift.start_time.asc(), BaristaShift.id.asc())
        )
    ).scalars().all()

    return AdminBootstrapOut(
        banners=[_serialize_banner(banner) for banner in banners],
        categories=[AdminCategoryOut.model_validate(category) for category in categories],
        baristas=[_serialize_barista(user) for user in baristas],
        barista_shifts=[_serialize_barista_shift(shift) for shift in barista_shifts],
        products=[_serialize_product(product) for product in products],
        program_settings=_serialize_program_settings(program_settings),
        app_settings=_serialize_app_settings(app_settings),
        reminder_settings=_serialize_reminder_settings(app_settings),
    )


@router.put("/api/admin/program-settings", response_model=AdminProgramsSettingsOut)
@router.put("/api/admin/loyalty-settings", response_model=AdminProgramsSettingsOut)
async def update_program_settings(
    payload: AdminProgramsSettingsIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminProgramsSettingsOut:
    loyalty_settings = await get_or_create_loyalty_settings(db)
    normalized = await _normalize_program_settings_payload(payload, db)

    loyalty_settings.classic_category_slug = normalized["classic_category_slug"]
    loyalty_settings.classic_category_slugs = normalized["classic_category_slugs"]
    loyalty_settings.paid_items_per_reward = normalized["paid_items_per_reward"]
    loyalty_settings.bonus_enabled = normalized["bonus_enabled"]
    loyalty_settings.bonus_earn_percent = normalized["bonus_earn_percent"]
    loyalty_settings.bonus_redeem_enabled = normalized["bonus_redeem_enabled"]
    loyalty_settings.bonus_redeem_max_percent = normalized["bonus_redeem_max_percent"]

    await db.commit()
    await db.refresh(loyalty_settings)
    return _serialize_program_settings(loyalty_settings)


@router.put("/api/admin/app-settings", response_model=AdminAppSettingsOut)
async def update_app_settings(
    payload: AdminAppSettingsIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAppSettingsOut:
    app_settings = await get_or_create_app_settings(db)
    for field_name, value in payload.model_dump().items():
        setattr(app_settings, field_name, value)

    await db.commit()
    await db.refresh(app_settings)
    return _serialize_app_settings(app_settings)


@router.get("/api/admin/reminders/settings", response_model=AdminReminderSettingsOut)
async def get_reminder_settings(
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminReminderSettingsOut:
    app_settings = await get_app_settings(db)
    return _serialize_reminder_settings(app_settings)


@router.put("/api/admin/reminders/settings", response_model=AdminReminderSettingsOut)
async def update_reminder_settings(
    payload: AdminReminderSettingsIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminReminderSettingsOut:
    app_settings = await get_or_create_app_settings(db)
    normalized = _normalize_reminder_settings_payload(payload)
    app_settings.inactive_reminder_enabled = bool(normalized["inactive_reminder_enabled"])
    app_settings.inactive_reminder_days = int(normalized["inactive_reminder_days"])
    app_settings.inactive_reminder_send_time = str(normalized["inactive_reminder_send_time"])
    app_settings.inactive_reminder_text = str(normalized["inactive_reminder_text"])
    await db.commit()
    await db.refresh(app_settings)
    return _serialize_reminder_settings(app_settings)


@router.get("/api/admin/analytics", response_model=AdminAnalyticsOut)
async def get_analytics(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnalyticsOut:
    resolved_from, resolved_to = _resolve_report_period(date_from, date_to)
    return await build_analytics(db, resolved_from, resolved_to)


@router.get("/api/admin/analytics/export.csv")
async def export_analytics_csv(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    resolved_from, resolved_to = _resolve_report_period(date_from, date_to)
    analytics = await build_analytics(db, resolved_from, resolved_to)
    content = build_analytics_csv_bytes(analytics)
    filename = f"coffee-analytics-{resolved_from.isoformat()}-{resolved_to.isoformat()}.csv"
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/admin/analytics/export.xlsx")
async def export_analytics_xlsx(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    resolved_from, resolved_to = _resolve_report_period(date_from, date_to)
    analytics = await build_analytics(db, resolved_from, resolved_to)
    content = build_analytics_xlsx_bytes(analytics)
    filename = f"coffee-analytics-{resolved_from.isoformat()}-{resolved_to.isoformat()}.xlsx"
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/api/admin/baristas",
    response_model=AdminBaristaOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_barista(
    payload: AdminBaristaIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBaristaOut:
    normalized = _normalize_barista_payload(payload)
    existing = None
    if normalized["telegram_id"] is not None:
        existing = await db.scalar(select(User).where(User.telegram_id == normalized["telegram_id"]))
    if existing is None:
        existing = await _find_unique_user_by_username(normalized["username"], db)
    if existing is None and not normalized["username"]:
        existing = await _find_unique_pending_barista_by_name(normalized["full_name"], db)
    if existing is None:
        telegram_id = int(normalized["telegram_id"]) if normalized["telegram_id"] is not None else await _reserve_placeholder_telegram_id(db)
        user = User(
            telegram_id=telegram_id,
            username=normalized["username"],
            full_name=normalized["full_name"],
            is_barista=bool(normalized["is_barista"]),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return _serialize_barista(user)

    if normalized["telegram_id"] is not None:
        existing.telegram_id = int(normalized["telegram_id"])
    existing.username = normalized["username"]
    existing.full_name = normalized["full_name"]
    existing.is_barista = bool(normalized["is_barista"])
    await db.commit()
    await db.refresh(existing)
    return _serialize_barista(existing)


@router.put("/api/admin/baristas/{user_id}", response_model=AdminBaristaOut)
async def update_barista(
    user_id: int,
    payload: AdminBaristaIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBaristaOut:
    user = await _get_barista_or_404(user_id, db)
    normalized = _normalize_barista_payload(payload)

    if normalized["telegram_id"] is not None:
        duplicate = await db.scalar(
            select(User).where(
                User.telegram_id == normalized["telegram_id"],
                User.id != user_id,
            )
        )
        if duplicate is not None:
            raise HTTPException(status_code=409, detail="Пользователь с таким Telegram ID уже существует.")

    if normalized["username"]:
        duplicate_by_username = await db.scalar(
            select(User).where(
                func.lower(User.username) == normalized["username"],
                User.telegram_id < 0,
                User.id != user_id,
            )
        )
        if duplicate_by_username is not None:
            raise HTTPException(status_code=409, detail="Уже есть ожидающая запись бариста с таким username.")
    elif is_placeholder_telegram_id(user.telegram_id):
        duplicate_by_name = await db.scalar(
            select(User).where(
                User.is_barista.is_(True),
                User.telegram_id < 0,
                or_(User.username.is_(None), User.username == ""),
                func.lower(User.full_name) == normalized["full_name"].lower(),
                User.id != user_id,
            )
        )
        if duplicate_by_name is not None:
            raise HTTPException(status_code=409, detail="Уже есть ожидающая запись бариста с таким именем.")

    if normalized["telegram_id"] is not None:
        user.telegram_id = int(normalized["telegram_id"])
    user.username = normalized["username"]
    user.full_name = normalized["full_name"]
    user.is_barista = bool(normalized["is_barista"])
    await db.commit()
    await db.refresh(user)
    return _serialize_barista(user)


@router.post(
    "/api/admin/barista-shifts",
    response_model=AdminBaristaShiftOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_barista_shift(
    payload: AdminBaristaShiftIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBaristaShiftOut:
    normalized = await _normalize_barista_shift_payload(payload, db)
    shift = BaristaShift(**normalized)
    db.add(shift)
    await db.commit()
    shift = await _get_barista_shift_or_404(shift.id, db)
    return _serialize_barista_shift(shift)


@router.put("/api/admin/barista-shifts/{shift_id}", response_model=AdminBaristaShiftOut)
async def update_barista_shift(
    shift_id: int,
    payload: AdminBaristaShiftIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBaristaShiftOut:
    shift = await _get_barista_shift_or_404(shift_id, db)
    normalized = await _normalize_barista_shift_payload(payload, db, exclude_shift_id=shift_id)

    shift.user_id = int(normalized["user_id"])
    shift.starts_at = normalized["starts_at"]
    shift.ends_at = normalized["ends_at"]
    shift.weekday = int(normalized["weekday"])
    shift.start_time = normalized["start_time"]
    shift.end_time = normalized["end_time"]
    shift.note = normalized["note"]
    shift.is_active = bool(normalized["is_active"])
    await db.commit()
    shift = await _get_barista_shift_or_404(shift_id, db)
    return _serialize_barista_shift(shift)


@router.delete("/api/admin/barista-shifts/{shift_id}")
async def delete_barista_shift(
    shift_id: int,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    shift = await _get_barista_shift_or_404(shift_id, db)
    await db.delete(shift)
    await db.commit()
    return {"ok": True}


@router.post(
    "/api/admin/banners",
    response_model=AdminBannerOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_banner(
    payload: AdminBannerIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBannerOut:
    banner = Banner(**_normalize_banner_payload(payload))
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    return _serialize_banner(banner)


@router.put("/api/admin/banners/{banner_id}", response_model=AdminBannerOut)
async def update_banner(
    banner_id: int,
    payload: AdminBannerIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBannerOut:
    banner = await _get_banner_or_404(banner_id, db)
    normalized = _normalize_banner_payload(payload)

    for key, value in normalized.items():
        setattr(banner, key, value)

    await db.commit()
    await db.refresh(banner)
    return _serialize_banner(banner)


@router.post(
    "/api/admin/categories",
    response_model=AdminCategoryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    payload: AdminCategoryIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCategoryOut:
    slug = _normalize_category_slug(payload.slug)
    name = _normalize_category_name(payload.name)
    existing = await db.scalar(select(Category).where(Category.slug == slug))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Категория с таким slug уже существует.")

    category = Category(
        slug=slug,
        name=name,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return AdminCategoryOut.model_validate(category)


@router.put("/api/admin/categories/{category_id}", response_model=AdminCategoryOut)
async def update_category(
    category_id: int,
    payload: AdminCategoryIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminCategoryOut:
    category = await db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Категория не найдена.")

    slug = _normalize_category_slug(payload.slug)
    name = _normalize_category_name(payload.name)
    existing = await db.scalar(select(Category).where(Category.slug == slug, Category.id != category_id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Категория с таким slug уже существует.")

    category.slug = slug
    category.name = name
    category.sort_order = payload.sort_order
    category.is_active = payload.is_active
    await db.commit()
    await db.refresh(category)
    return AdminCategoryOut.model_validate(category)


@router.post(
    "/api/admin/products",
    response_model=AdminProductOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    payload: AdminProductIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminProductOut:
    normalized = _normalize_product_payload(payload)
    await _get_category_or_none(normalized["category_id"], db)

    product = Product(**normalized)
    db.add(product)
    await db.commit()
    product = await _get_product_or_404(product.id, db)
    return _serialize_product(product)


@router.put("/api/admin/products/{product_id}", response_model=AdminProductOut)
async def update_product(
    product_id: int,
    payload: AdminProductIn,
    _: User | None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminProductOut:
    product = await _get_product_or_404(product_id, db)
    normalized = _normalize_product_payload(payload)
    await _get_category_or_none(normalized["category_id"], db)

    for key, value in normalized.items():
        setattr(product, key, value)

    await db.commit()
    product = await _get_product_or_404(product_id, db)
    return _serialize_product(product)


@router.post("/api/admin/uploads/images", response_model=AdminUploadOut)
async def upload_image(
    file: UploadFile = File(...),
    _: User | None = Depends(require_admin),
) -> AdminUploadOut:
    extension = _resolve_upload_extension(file.filename, file.content_type)

    try:
        content = await file.read()
    finally:
        await file.close()

    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой.")
    if len(content) > MAX_IMAGE_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Изображение не должно быть больше 5 МБ.")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    target_path = UPLOADS_DIR / filename
    target_path.write_bytes(content)

    return AdminUploadOut(url=f"/static/uploads/{filename}")
