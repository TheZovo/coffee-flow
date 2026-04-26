from __future__ import annotations

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.bot import edit_user_message, send_to_user
from app.config import settings
from app.database import SessionLocal
from app.models import ConsumptionPlace, Order, OrderStatus, OrderType, User
from app.services.app_settings import get_app_settings, render_text
from app.services.barista_access import (
    BaristaAccessState,
    claim_pending_barista_profile,
    format_shift_datetime,
    format_shift_range,
    get_active_barista_chat_ids,
    get_barista_access_state,
)
from app.services.order_management import apply_order_status, find_order_by_number, today_local_date

barista_dp = Dispatcher()
barista_bot = Bot(token=settings.TELEGRAM_BARISTA_BOT_TOKEN) if settings.TELEGRAM_BARISTA_BOT_TOKEN else None


def _name_from_user(from_user) -> str | None:
    if from_user is None:
        return None
    first_name = getattr(from_user, "first_name", "") or ""
    last_name = getattr(from_user, "last_name", "") or ""
    full_name = f"{first_name} {last_name}".strip()
    return full_name or None


def _money(cents: int) -> str:
    return f"{cents / 100:.2f} BYN"


def _setting_text(value: str | None, fallback: str) -> str:
    normalized = (value or "").strip()
    return normalized or fallback


def _sync_barista_profile(user: User | None, from_user) -> bool:
    if user is None or from_user is None:
        return False

    changed = False
    username = getattr(from_user, "username", None)
    full_name = _name_from_user(from_user)
    if user.username != username:
        user.username = username
        changed = True
    if full_name and user.full_name != full_name:
        user.full_name = full_name
        changed = True
    return changed


async def _load_barista_access(session: AsyncSession, from_user) -> BaristaAccessState:
    if from_user is None:
        return BaristaAccessState(user=None, active_shift=None, next_shift=None)

    changed = await claim_pending_barista_profile(
        session=session,
        telegram_id=from_user.id,
        username=getattr(from_user, "username", None),
        full_name=_name_from_user(from_user),
    )
    access = await get_barista_access_state(session, from_user.id)
    if changed or _sync_barista_profile(access.user, from_user):
        await session.commit()
    return access


def _build_access_context(access: BaristaAccessState) -> dict[str, str]:
    active_shift_label = format_shift_range(access.active_shift)
    next_shift_label = format_shift_range(access.next_shift)
    shift_start_label = format_shift_datetime(access.active_shift) if access.active_shift else ""
    shift_end_label = access.active_shift.end_time.strftime("%H:%M") if access.active_shift else ""

    if access.can_access and access.active_shift is not None:
        access_summary = f"Ваша смена активна: {active_shift_label}."
        shift_hint = f"Доступ к боту открыт до {format_shift_datetime(access.active_shift.ends_at)}."
    elif access.is_registered and access.next_shift is not None:
        access_summary = f"Сейчас вы вне смены. Ближайшая смена: {next_shift_label}."
        shift_hint = f"Доступ откроется автоматически в {format_shift_datetime(access.next_shift.starts_at)}."
    elif access.is_registered:
        access_summary = "Сейчас у вас нет назначенной активной смены."
        shift_hint = "Попросите владельца назначить или продлить вашу смену в админ-панели."
    else:
        access_summary = "Ваш аккаунт еще не добавлен в команду бариста."
        shift_hint = "Попросите владельца добавить вас в команду и назначить смену."

    return {
        "access_summary": access_summary,
        "shift_hint": shift_hint,
        "active_shift_label": active_shift_label,
        "next_shift_label": next_shift_label,
        "shift_start_label": shift_start_label,
        "shift_end_label": shift_end_label,
    }

def _build_access_context(access: BaristaAccessState) -> dict[str, str]:
    active_shift_label = format_shift_range(access.active_shift)
    next_shift_label = format_shift_range(access.next_shift)
    shift_start_label = format_shift_datetime(access.active_shift) if access.active_shift else ""
    shift_end_label = access.active_shift.end_time.strftime("%H:%M") if access.active_shift else ""

    if access.can_access and access.active_shift is not None:
        access_summary = f"Ваша смена активна: {active_shift_label}."
        shift_hint = f"Доступ к боту открыт до {shift_end_label}."
    elif access.is_registered and access.next_shift is not None:
        access_summary = f"Сейчас вы вне смены. Ближайшая смена: {next_shift_label}."
        shift_hint = f"Доступ откроется автоматически в {format_shift_datetime(access.next_shift)}."
    elif access.is_registered:
        access_summary = "Сейчас у вас нет активной смены по расписанию."
        shift_hint = "Попросите владельца настроить ваше недельное расписание в админ-панели."
    else:
        access_summary = "Ваш аккаунт еще не добавлен в команду бариста."
        shift_hint = "Попросите владельца добавить вас в команду и настроить расписание."

    return {
        "access_summary": access_summary,
        "shift_hint": shift_hint,
        "active_shift_label": active_shift_label,
        "next_shift_label": next_shift_label,
        "shift_start_label": shift_start_label,
        "shift_end_label": shift_end_label,
    }


def _render_with_access(template: str | None, fallback: str, access: BaristaAccessState, **values: object) -> str:
    return render_text(template or fallback, **_build_access_context(access), **values)


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


async def _load_app_settings(session: AsyncSession | None = None):
    if session is not None:
        return await get_app_settings(session)

    async with SessionLocal() as local_session:
        return await get_app_settings(local_session)


def _order_keyboard(order: Order, app_settings) -> InlineKeyboardMarkup | None:
    if order.status in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}:
        return None

    buttons: list[InlineKeyboardButton] = []
    if order.status == OrderStatus.NEW:
        buttons.append(
            InlineKeyboardButton(
                text=_setting_text(app_settings.barista_action_take_text, "👨‍🍳 В работу"),
                callback_data=f"barista:take:{order.id}",
            )
        )
    if order.status in {OrderStatus.NEW, OrderStatus.IN_PROGRESS}:
        buttons.append(
            InlineKeyboardButton(
                text=_setting_text(app_settings.barista_action_ready_text, "✅ Готов"),
                callback_data=f"barista:ready:{order.id}",
            )
        )
    if order.status == OrderStatus.READY and order.order_type == OrderType.DELIVERY:
        buttons.append(
            InlineKeyboardButton(
                text=_setting_text(app_settings.barista_action_route_text, "🚚 В пути"),
                callback_data=f"barista:route:{order.id}",
            )
        )
    if order.status in {OrderStatus.READY, OrderStatus.EN_ROUTE}:
        buttons.append(
            InlineKeyboardButton(
                text=_setting_text(app_settings.barista_action_done_text, "🎉 Выдан"),
                callback_data=f"barista:done:{order.id}",
            )
        )
    buttons.append(
        InlineKeyboardButton(
            text=_setting_text(app_settings.barista_action_cancel_text, "✖️ Отменить"),
            callback_data=f"barista:cancel:{order.id}",
        )
    )

    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def _pickup_text(order: Order, app_settings) -> str:
    if order.pickup_label:
        return order.pickup_label
    if order.scheduled_for is not None:
        return order.scheduled_for.strftime("%d.%m %H:%M")
    return _setting_text(app_settings.pickup_asap_text, "Как можно скорее")


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


def _build_order_context(order: Order, app_settings) -> dict[str, str]:
    return {
        "order_number": order.order_number,
        "status_label": _status_label(order.status, app_settings),
        "order_type_label": _order_type_label(order.order_type, app_settings),
        "consumption_place_label": _consumption_place_label(order.consumption_place),
        "contact_name": order.contact_name or _setting_text(app_settings.order_contact_name_fallback, "Без имени"),
        "contact_phone": order.contact_phone or _setting_text(app_settings.order_contact_phone_fallback, "-"),
        "pickup_label": _pickup_text(order, app_settings),
        "items_list": "\n".join(f"• {item.name_snapshot} x{item.qty}" for item in order.items)
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


def _order_text(order: Order, app_settings) -> str:
    fallback_template = (
        "☕ Заказ №{order_number}\n"
        "Статус: {status_label}\n"
        "Формат: {order_type_label}\n"
        "Клиент: {contact_name}\n"
        "Телефон: {contact_phone}\n"
        "Когда заберут: {pickup_label}{delivery_address_block}{delivery_comment_block}\n\n"
        "Состав:\n{items_list}\n\n"
        "Сумма: {total}\n"
        "Скидки: {discount_total}\n"
        "{promo_line}{loyalty_line}{bonus_spent_line}"
        "К оплате: {final_total}\n"
        "{bonus_earned_line}{note_line}"
    )
    context = _build_order_context(order, app_settings)
    rendered = render_text(app_settings.barista_order_card_text or fallback_template, **context)
    return _with_consumption_place(rendered, context["consumption_place_label"])


async def _load_order(session: AsyncSession, order_id: int) -> Order | None:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.user), joinedload(Order.branch), joinedload(Order.items))
        .where(Order.id == order_id)
    )
    return result.unique().scalar_one_or_none()


def _customer_status_message(order: Order, app_settings) -> str:
    context = _build_order_context(order, app_settings)
    template_map = {
        OrderStatus.IN_PROGRESS: app_settings.customer_status_in_progress_text,
        OrderStatus.READY: app_settings.customer_status_ready_text,
        OrderStatus.EN_ROUTE: app_settings.customer_status_en_route_text,
        OrderStatus.COMPLETED: app_settings.customer_status_completed_text,
        OrderStatus.CANCELLED: app_settings.customer_status_cancelled_text,
    }
    template = template_map.get(order.status)
    if template:
        return render_text(template, **context)
    return render_text("ℹ️ Статус заказа №{order_number} обновлен: {status_label}.", **context)


async def _save_customer_message_meta(order_id: int, message_id: int, status: str) -> None:
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            return
        order.customer_last_message_id = message_id
        order.customer_last_message_status = status
        await session.commit()


async def _notify_customer_status_update(order: Order, app_settings) -> None:
    if order.user is None:
        return

    customer_text = _customer_status_message(order, app_settings)
    if not customer_text:
        return

    if (
        order.status == OrderStatus.COMPLETED
        and order.customer_last_message_id is not None
        and order.customer_last_message_status == OrderStatus.READY.value
    ):
        edited_message = await edit_user_message(
            order.user.telegram_id,
            order.customer_last_message_id,
            customer_text,
        )
        if edited_message is not None:
            await _save_customer_message_meta(
                order.id,
                order.customer_last_message_id,
                OrderStatus.COMPLETED.value,
            )
            return

    sent_message = await send_to_user(order.user.telegram_id, customer_text)
    if sent_message is not None:
        await _save_customer_message_meta(order.id, sent_message.message_id, order.status.value)


async def send_to_baristas(text: str, order_id: int | None = None) -> None:
    if barista_bot is None:
        return

    chat_ids: set[int] = set()
    if settings.BARISTA_CHAT_ID is not None:
        chat_ids.add(settings.BARISTA_CHAT_ID)

    async with SessionLocal() as session:
        chat_ids.update(await get_active_barista_chat_ids(session))
        order = await _load_order(session, order_id) if order_id is not None else None
        app_settings = await get_app_settings(session)

    reply_markup = _order_keyboard(order, app_settings) if order is not None else None
    for chat_id in chat_ids:
        try:
            await barista_bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        except Exception:
            continue


@barista_dp.message(CommandStart())
async def start_command(message: Message) -> None:
    async with SessionLocal() as session:
        app_settings = await get_app_settings(session)
        access = await _load_barista_access(session, message.from_user)
        await message.answer(
            _render_with_access(
                app_settings.barista_start_text,
                (
                    "👋 Бариста-бот Coffee Flow\n\n"
                    "{access_summary}\n"
                    "{shift_hint}\n\n"
                    "Команды:\n"
                    "/login - проверить доступ к смене\n"
                    "/queue - активные заказы\n"
                    "/order <номер> - открыть заказ\n"
                    "/today - статистика за сегодня\n"
                    "/logout - выйти из диалога"
                ),
                access,
            )
        )


@barista_dp.message(Command("login"))
async def login_command(message: Message) -> None:
    if not message.from_user:
        return

    async with SessionLocal() as session:
        app_settings = await get_app_settings(session)
        access = await _load_barista_access(session, message.from_user)
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip():
            await message.answer(
                _render_with_access(
                    app_settings.barista_login_invalid_text,
                    "ℹ️ Секрет больше не нужен. Доступ определяется активной сменой владельцем кофейни.",
                    access,
                )
            )
            return

        if not access.can_access:
            await message.answer(
                _render_with_access(
                    app_settings.barista_access_denied_text,
                    "⛔ Доступ к боту закрыт.\n{shift_hint}",
                    access,
                )
            )
            return

        await message.answer(
            _render_with_access(
                app_settings.barista_login_success_text,
                "✅ Доступ подтвержден. Ваша смена активна до {shift_end_label}. Используйте /queue для работы с заказами.",
                access,
            )
        )


@barista_dp.message(Command("logout"))
async def logout_command(message: Message) -> None:
    async with SessionLocal() as session:
        app_settings = await get_app_settings(session)
        access = await _load_barista_access(session, message.from_user)
        await message.answer(
            _render_with_access(
                app_settings.barista_logout_text,
                "👋 Вы вышли из диалога. Доступ к заказам снова открывается только во время вашей смены.",
                access,
            )
        )


@barista_dp.message(Command("queue"))
async def queue_command(message: Message) -> None:
    if not message.from_user:
        return

    async with SessionLocal() as session:
        app_settings = await get_app_settings(session)
        access = await _load_barista_access(session, message.from_user)
        if not access.can_access:
            await message.answer(
                _render_with_access(
                    app_settings.barista_access_denied_text,
                    "⛔ Доступ к боту закрыт.\n{shift_hint}",
                    access,
                )
            )
            return

        result = await session.execute(
            select(Order)
            .options(joinedload(Order.user), joinedload(Order.branch), joinedload(Order.items))
            .where(~Order.status.in_([OrderStatus.COMPLETED, OrderStatus.CANCELLED]))
            .order_by(Order.created_at.asc())
            .limit(20)
        )
        orders = result.unique().scalars().all()

        if not orders:
            await message.answer(render_text(app_settings.barista_queue_empty_text))
            return

        await message.answer(
            render_text(app_settings.barista_queue_summary_text, orders_count=len(orders))
        )
        for order in orders:
            await message.answer(_order_text(order, app_settings), reply_markup=_order_keyboard(order, app_settings))


@barista_dp.message(Command("order"))
async def order_command(message: Message) -> None:
    if not message.from_user:
        return

    async with SessionLocal() as session:
        app_settings = await get_app_settings(session)
        access = await _load_barista_access(session, message.from_user)
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(render_text(app_settings.barista_order_usage_text))
            return

        if not access.can_access:
            await message.answer(
                _render_with_access(
                    app_settings.barista_access_denied_text,
                    "⛔ Доступ к боту закрыт.\n{shift_hint}",
                    access,
                )
            )
            return

        order = await find_order_by_number(session, parts[1].strip(), prefer_today=True)
        if order is None:
            await message.answer(render_text(app_settings.barista_order_not_found_text))
            return

        await message.answer(_order_text(order, app_settings), reply_markup=_order_keyboard(order, app_settings))


@barista_dp.message(Command("today"))
async def today_command(message: Message) -> None:
    if not message.from_user:
        return

    async with SessionLocal() as session:
        app_settings = await get_app_settings(session)
        access = await _load_barista_access(session, message.from_user)
        if not access.can_access:
            await message.answer(
                _render_with_access(
                    app_settings.barista_access_denied_text,
                    "⛔ Доступ к боту закрыт.\n{shift_hint}",
                    access,
                )
            )
            return

        result = await session.execute(select(Order).where(Order.order_day == today_local_date()))
        orders = result.scalars().all()

        if not orders:
            await message.answer(render_text(app_settings.barista_today_empty_text))
            return

        counts: dict[OrderStatus, int] = {status: 0 for status in OrderStatus}
        revenue_cents = 0
        for order in orders:
            counts[order.status] += 1
            if order.status == OrderStatus.COMPLETED:
                revenue_cents += order.final_cents

        await message.answer(
            render_text(
                app_settings.barista_today_summary_text,
                orders_count=len(orders),
                new_count=counts[OrderStatus.NEW],
                in_progress_count=counts[OrderStatus.IN_PROGRESS],
                ready_count=counts[OrderStatus.READY],
                en_route_count=counts[OrderStatus.EN_ROUTE],
                completed_count=counts[OrderStatus.COMPLETED],
                cancelled_count=counts[OrderStatus.CANCELLED],
                revenue_total=_money(revenue_cents),
            )
        )


@barista_dp.callback_query(F.data.startswith("barista:"))
async def order_callback(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.data:
        return

    async with SessionLocal() as session:
        app_settings = await get_app_settings(session)

        _, action, order_id_raw = callback.data.split(":", 2)
        try:
            order_id = int(order_id_raw)
        except ValueError:
            await callback.answer(render_text(app_settings.barista_invalid_order_id_text), show_alert=True)
            return

        status_map = {
            "take": OrderStatus.IN_PROGRESS,
            "ready": OrderStatus.READY,
            "route": OrderStatus.EN_ROUTE,
            "done": OrderStatus.COMPLETED,
            "cancel": OrderStatus.CANCELLED,
        }
        new_status = status_map.get(action)
        if new_status is None:
            await callback.answer(render_text(app_settings.barista_unknown_action_text), show_alert=True)
            return

        access = await _load_barista_access(session, callback.from_user)
        if not access.can_access:
            await callback.answer(
                _render_with_access(
                    app_settings.barista_access_denied_text,
                    "⛔ Доступ к боту закрыт.\n{shift_hint}",
                    access,
                ),
                show_alert=True,
            )
            return

        order = await _load_order(session, order_id)
        if order is None:
            await callback.answer(render_text(app_settings.barista_order_not_found_text), show_alert=True)
            return

        if order.status in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}:
            await callback.answer(render_text(app_settings.barista_order_closed_text), show_alert=True)
            return

        if order.order_type != OrderType.DELIVERY and new_status == OrderStatus.EN_ROUTE:
            await callback.answer(render_text(app_settings.barista_delivery_only_status_text), show_alert=True)
            return

        updated_order = await apply_order_status(session, order, new_status)
        refreshed_order = await _load_order(session, updated_order.id)
        if refreshed_order is None:
            await callback.answer(render_text(app_settings.barista_order_reload_error_text), show_alert=True)
            return

    if callback.message is not None:
        try:
            await callback.message.edit_text(
                _order_text(refreshed_order, app_settings),
                reply_markup=_order_keyboard(refreshed_order, app_settings),
            )
        except Exception:
            pass

    if refreshed_order.user is not None:
        await _notify_customer_status_update(refreshed_order, app_settings)

    await callback.answer(
        render_text(
            app_settings.barista_status_updated_text,
            status_label=_status_label(refreshed_order.status, app_settings),
        )
    )
