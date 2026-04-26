from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppSettings

APP_SETTINGS_SINGLETON_ID = 1

DEFAULT_APP_SETTINGS: dict[str, str] = {
    "miniapp_button_text": "☕ Открыть Coffee Flow",
    "customer_start_text": (
        "☕ Добро пожаловать в Coffee Flow!\n\n"
        "Откройте Mini App по кнопке ниже: внутри меню, корзина, заказы и быстрый самовывоз без очереди."
    ),
    "customer_app_text": "🚀 Открыть Mini App можно по кнопке ниже.",
    "customer_help_text": (
        "📌 Команды:\n"
        "/start - главное сообщение\n"
        "/app - открыть Mini App\n"
        "/help - помощь"
    ),
    "customer_contact_request_text": "📱 Отправьте, пожалуйста, свой номер через Telegram.",
    "customer_phone_error_text": "⚠️ Не удалось прочитать номер телефона. Попробуйте еще раз.",
    "customer_phone_saved_text": "✅ Телефон сохранен. Возвращайтесь в Mini App и оформляйте заказ.",
    "customer_order_created_text": (
        "🧾 Заказ №{order_number} принят.\n"
        "⏰ Самовывоз: {pickup_label}\n"
        "💳 К оплате: {final_total}\n\n"
        "Следующий статус пришлем прямо сюда."
    ),
    "customer_status_in_progress_text": "👨‍🍳 Заказ №{order_number} принят в работу. Начинаем готовить.",
    "customer_status_ready_text": "✅ Заказ №{order_number} готов.\nМожно подходить за самовывозом.",
    "customer_status_en_route_text": "🚚 Заказ №{order_number} передан в доставку.",
    "customer_status_completed_text": (
        "🎉 Заказ №{order_number} завершен.\n"
        "💎 Начислено бонусов: {bonus_earned}."
    ),
    "customer_status_cancelled_text": (
        "⚠️ Заказ №{order_number} отменен. Если списывались бонусы, они уже возвращены."
    ),
    "barista_start_text": (
        "👋 Бариста-бот Coffee Flow\n\n"
        "{access_summary}\n"
        "{shift_hint}\n\n"
        "Команды:\n"
        "/login - проверить доступ к текущей смене\n"
        "/queue - активные заказы\n"
        "/order <номер> - открыть заказ\n"
        "/today - статистика за сегодня\n"
        "/logout - выйти из диалога"
    ),
    "barista_login_invalid_text": "ℹ️ Секрет больше не нужен. Доступ к боту открывается автоматически только во время вашей смены.",
    "barista_login_success_text": "✅ Доступ подтвержден. Ваша смена активна до {shift_end_label}. Используйте /queue для управления заказами.",
    "barista_logout_text": "👋 Вы вышли из диалога. Доступ к заказам снова открывается только во время вашей смены.",
    "barista_access_denied_text": "⛔ Доступ к боту закрыт.\n{shift_hint}",
    "barista_queue_empty_text": "☕ Активных заказов нет.",
    "barista_queue_summary_text": "📋 Активных заказов: {orders_count}",
    "barista_order_usage_text": "ℹ️ Использование: /order <номер>",
    "barista_order_not_found_text": "🔎 Заказ не найден.",
    "barista_today_empty_text": "📭 За сегодня заказов пока нет.",
    "barista_today_summary_text": (
        "📊 За сегодня: {orders_count} заказов\n"
        "Новые: {new_count}\n"
        "В работе: {in_progress_count}\n"
        "Готовы: {ready_count}\n"
        "В пути: {en_route_count}\n"
        "Завершены: {completed_count}\n"
        "Отменены: {cancelled_count}\n"
        "Выручка по завершенным: {revenue_total}"
    ),
    "barista_user_not_found_text": "🙈 Пользователь не найден.",
    "barista_invalid_order_id_text": "⚠️ Некорректный идентификатор заказа.",
    "barista_unknown_action_text": "⚠️ Неизвестное действие.",
    "barista_order_closed_text": "🧾 Этот заказ уже закрыт.",
    "barista_delivery_only_status_text": "🚫 Для самовывоза этот статус не используется.",
    "barista_order_reload_error_text": "⚠️ Заказ не найден после обновления.",
    "barista_status_updated_text": "✅ Статус обновлен: {status_label}",
    "pickup_asap_text": "Как можно скорее",
    "order_type_pickup_label": "Самовывоз",
    "order_type_delivery_label": "Доставка",
    "order_status_new_label": "Новый",
    "order_status_in_progress_label": "В работе",
    "order_status_ready_label": "Готов",
    "order_status_en_route_label": "В пути",
    "order_status_completed_label": "Завершен",
    "order_status_cancelled_label": "Отменен",
    "order_contact_name_fallback": "Без имени",
    "order_contact_phone_fallback": "-",
    "order_empty_items_text": "• Нет позиций",
    "order_promo_label": "Промо",
    "order_loyalty_label": "Лояльность",
    "order_bonus_spent_label": "Списано бонусами",
    "order_bonus_earned_label": "К начислению бонусов",
    "order_note_label": "Комментарий клиента",
    "order_delivery_address_label": "Адрес",
    "order_delivery_comment_label": "Комментарий к доставке",
    "barista_action_take_text": "🧑‍🍳 В работу",
    "barista_action_ready_text": "✅ Готов",
    "barista_action_route_text": "🚚 В пути",
    "barista_action_done_text": "🎉 Выдан",
    "barista_action_cancel_text": "✖️ Отменить",
    "barista_order_card_text": (
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
    ),
    "barista_new_order_text": (
        "🆕 Новый заказ №{order_number}\n"
        "Формат: {order_type_label}\n"
        "Клиент: {contact_name}\n"
        "Телефон: {contact_phone}\n"
        "Когда заберут: {pickup_label}\n\n"
        "Состав:\n{items_list}\n\n"
        "{promo_line}{loyalty_line}{bonus_spent_line}"
        "Скидка всего: {discount_total}\n"
        "К оплате: {final_total}\n"
        "{bonus_earned_line}{note_line}"
    ),
}
APP_SETTINGS_FIELDS: tuple[str, ...] = tuple(DEFAULT_APP_SETTINGS.keys())
LEGACY_APP_SETTINGS_REPLACEMENTS: dict[str, set[str]] = {
    "barista_start_text": {
        (
            "👋 Бариста-бот Coffee Flow\n\n"
            "Команды:\n"
            "/login <секрет> - включить доступ\n"
            "/queue - активные заказы\n"
            "/order <номер> - открыть заказ\n"
            "/today - статистика за сегодня\n"
            "/logout - отключить доступ"
        ),
    },
    "barista_login_invalid_text": {
        "🔐 Неверный секрет. Использование: /login <секрет>",
    },
    "barista_login_success_text": {
        "✅ Доступ включен. Используйте /queue для управления заказами.",
    },
    "barista_logout_text": {
        "👋 Доступ бариста отключен.",
    },
    "barista_access_denied_text": {
        "⛔ Доступ закрыт. Сначала выполните /login <секрет>.",
    },
}


def _apply_defaults(app_settings: AppSettings) -> AppSettings:
    for key, value in DEFAULT_APP_SETTINGS.items():
        current_value = getattr(app_settings, key, None)
        if current_value is None or current_value in LEGACY_APP_SETTINGS_REPLACEMENTS.get(key, set()):
            setattr(app_settings, key, value)
    return app_settings


async def get_app_settings(db: AsyncSession) -> AppSettings:
    app_settings = await db.scalar(select(AppSettings).where(AppSettings.id == APP_SETTINGS_SINGLETON_ID))
    if app_settings is not None:
        return _apply_defaults(app_settings)

    return AppSettings(id=APP_SETTINGS_SINGLETON_ID, **DEFAULT_APP_SETTINGS)


async def get_or_create_app_settings(db: AsyncSession) -> AppSettings:
    app_settings = await db.scalar(select(AppSettings).where(AppSettings.id == APP_SETTINGS_SINGLETON_ID))
    if app_settings is not None:
        return _apply_defaults(app_settings)

    app_settings = AppSettings(id=APP_SETTINGS_SINGLETON_ID, **DEFAULT_APP_SETTINGS)
    db.add(app_settings)
    await db.flush()
    return app_settings


def render_text(template: str | None, **values: object) -> str:
    safe_values = defaultdict(str, {key: "" if value is None else str(value) for key, value in values.items()})
    return str(template or "").format_map(safe_values).strip()
