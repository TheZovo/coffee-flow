from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.config import settings
from app.services.menu import default_addon_option_payloads, serialize_option_payloads


async def _column_exists(conn: AsyncConnection, table_name: str, column_name: str) -> bool:
    result = await conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
              AND column_name = :column_name
            LIMIT 1
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar_one_or_none() is not None


async def run_startup_migrations(conn: AsyncConnection) -> None:
    default_size_options_json = "[]"
    default_addon_options_json = serialize_option_payloads(default_addon_option_payloads())
    app_settings_columns = {
        "miniapp_button_text": "TEXT",
        "customer_start_text": "TEXT",
        "customer_app_text": "TEXT",
        "customer_help_text": "TEXT",
        "customer_contact_request_text": "TEXT",
        "customer_phone_error_text": "TEXT",
        "customer_phone_saved_text": "TEXT",
        "customer_order_created_text": "TEXT",
        "customer_status_in_progress_text": "TEXT",
        "customer_status_ready_text": "TEXT",
        "customer_status_en_route_text": "TEXT",
        "customer_status_completed_text": "TEXT",
        "customer_status_cancelled_text": "TEXT",
        "barista_start_text": "TEXT",
        "barista_login_invalid_text": "TEXT",
        "barista_login_success_text": "TEXT",
        "barista_logout_text": "TEXT",
        "barista_access_denied_text": "TEXT",
        "barista_queue_empty_text": "TEXT",
        "barista_queue_summary_text": "TEXT",
        "barista_order_usage_text": "TEXT",
        "barista_order_not_found_text": "TEXT",
        "barista_today_empty_text": "TEXT",
        "barista_today_summary_text": "TEXT",
        "barista_user_not_found_text": "TEXT",
        "barista_invalid_order_id_text": "TEXT",
        "barista_unknown_action_text": "TEXT",
        "barista_order_closed_text": "TEXT",
        "barista_delivery_only_status_text": "TEXT",
        "barista_order_reload_error_text": "TEXT",
        "barista_status_updated_text": "TEXT",
        "pickup_asap_text": "TEXT",
        "order_type_pickup_label": "TEXT",
        "order_type_delivery_label": "TEXT",
        "order_status_new_label": "TEXT",
        "order_status_in_progress_label": "TEXT",
        "order_status_ready_label": "TEXT",
        "order_status_en_route_label": "TEXT",
        "order_status_completed_label": "TEXT",
        "order_status_cancelled_label": "TEXT",
        "order_contact_name_fallback": "TEXT",
        "order_contact_phone_fallback": "TEXT",
        "order_empty_items_text": "TEXT",
        "order_promo_label": "TEXT",
        "order_loyalty_label": "TEXT",
        "order_bonus_spent_label": "TEXT",
        "order_bonus_earned_label": "TEXT",
        "order_note_label": "TEXT",
        "order_delivery_address_label": "TEXT",
        "order_delivery_comment_label": "TEXT",
        "barista_action_take_text": "TEXT",
        "barista_action_ready_text": "TEXT",
        "barista_action_route_text": "TEXT",
        "barista_action_done_text": "TEXT",
        "barista_action_cancel_text": "TEXT",
        "barista_order_card_text": "TEXT",
        "barista_new_order_text": "TEXT",
    }

    result = await conn.execute(
        text(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'users'
              AND column_name = 'telegram_id'
            """
        )
    )
    data_type = result.scalar_one_or_none()

    if data_type == "integer":
        await conn.execute(
            text(
                """
                ALTER TABLE users
                ALTER COLUMN telegram_id TYPE BIGINT
                USING telegram_id::bigint
                """
            )
        )

    await conn.execute(
        text(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS bonus_balance INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS loyalty_paid_coffee_count INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS loyalty_free_coffee_count INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS inactive_reminder_sent_at TIMESTAMPTZ
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS customer_last_message_id BIGINT
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS customer_last_message_status VARCHAR(32)
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS barista_shifts (
                id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                starts_at TIMESTAMPTZ NOT NULL,
                ends_at TIMESTAMPTZ NOT NULL,
                note VARCHAR(255),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_barista_shifts_user_time
            ON barista_shifts (user_id, starts_at, ends_at)
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_barista_shifts_active_window
            ON barista_shifts (is_active, starts_at, ends_at)
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE barista_shifts
            ADD COLUMN IF NOT EXISTS weekday INTEGER
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE barista_shifts
            ADD COLUMN IF NOT EXISTS start_time TIME
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE barista_shifts
            ADD COLUMN IF NOT EXISTS end_time TIME
            """
        )
    )
    await conn.execute(
        text(
            f"""
            UPDATE barista_shifts
            SET
                weekday = CASE
                    WHEN weekday IS NOT NULL THEN weekday
                    WHEN EXTRACT(ISODOW FROM starts_at AT TIME ZONE '{settings.APP_TIMEZONE}')::int = 7 THEN 6
                    ELSE EXTRACT(ISODOW FROM starts_at AT TIME ZONE '{settings.APP_TIMEZONE}')::int - 1
                END,
                start_time = COALESCE(start_time, (starts_at AT TIME ZONE '{settings.APP_TIMEZONE}')::time),
                end_time = COALESCE(end_time, (ends_at AT TIME ZONE '{settings.APP_TIMEZONE}')::time)
            WHERE weekday IS NULL OR start_time IS NULL OR end_time IS NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE barista_shifts
            SET weekday = 0
            WHERE weekday IS NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE barista_shifts
            SET start_time = TIME '09:00'
            WHERE start_time IS NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE barista_shifts
            SET end_time = TIME '18:00'
            WHERE end_time IS NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE barista_shifts
            ALTER COLUMN weekday SET NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE barista_shifts
            ALTER COLUMN start_time SET NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE barista_shifts
            ALTER COLUMN end_time SET NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_barista_shifts_user_weekday_time
            ON barista_shifts (user_id, weekday, start_time, end_time)
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_barista_shifts_active_weekday_time
            ON barista_shifts (is_active, weekday, start_time, end_time)
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS loyalty_settings (
                id INTEGER PRIMARY KEY,
                classic_category_slug VARCHAR(80) NOT NULL DEFAULT 'coffee',
                classic_category_slugs TEXT NOT NULL DEFAULT 'coffee',
                paid_items_per_reward INTEGER NOT NULL DEFAULT 5,
                bonus_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                bonus_earn_percent INTEGER NOT NULL DEFAULT 5,
                bonus_redeem_enabled BOOLEAN NOT NULL DEFAULT TRUE
            )
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE loyalty_settings
            ADD COLUMN IF NOT EXISTS classic_category_slugs TEXT NOT NULL DEFAULT 'coffee'
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE loyalty_settings
            ADD COLUMN IF NOT EXISTS bonus_enabled BOOLEAN NOT NULL DEFAULT TRUE
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE loyalty_settings
            ADD COLUMN IF NOT EXISTS bonus_earn_percent INTEGER NOT NULL DEFAULT 5
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE loyalty_settings
            ADD COLUMN IF NOT EXISTS bonus_redeem_enabled BOOLEAN NOT NULL DEFAULT TRUE
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE loyalty_settings
            ADD COLUMN IF NOT EXISTS bonus_redeem_max_percent INTEGER NOT NULL DEFAULT 100
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE loyalty_settings
            SET classic_category_slugs = COALESCE(NULLIF(classic_category_slugs, ''), classic_category_slug, 'coffee')
            """
        )
    )
    await conn.execute(
        text(
            """
            INSERT INTO loyalty_settings (
                id,
                classic_category_slug,
                classic_category_slugs,
                paid_items_per_reward,
                bonus_enabled,
                bonus_earn_percent,
                bonus_redeem_enabled
            )
            VALUES (1, 'coffee', 'coffee', 5, TRUE, 5, TRUE)
            ON CONFLICT (id) DO NOTHING
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY,
                miniapp_button_text TEXT,
                customer_start_text TEXT,
                customer_app_text TEXT,
                customer_help_text TEXT,
                customer_contact_request_text TEXT,
                customer_phone_error_text TEXT,
                customer_phone_saved_text TEXT,
                customer_order_created_text TEXT,
                customer_status_in_progress_text TEXT,
                customer_status_ready_text TEXT,
                customer_status_en_route_text TEXT,
                customer_status_completed_text TEXT,
                customer_status_cancelled_text TEXT,
                barista_start_text TEXT,
                barista_login_invalid_text TEXT,
                barista_login_success_text TEXT,
                barista_logout_text TEXT,
                barista_access_denied_text TEXT,
                barista_queue_empty_text TEXT,
                barista_queue_summary_text TEXT,
                barista_order_usage_text TEXT,
                barista_order_not_found_text TEXT,
                barista_today_empty_text TEXT,
                barista_today_summary_text TEXT,
                barista_user_not_found_text TEXT,
                barista_invalid_order_id_text TEXT,
                barista_unknown_action_text TEXT,
                barista_order_closed_text TEXT,
                barista_delivery_only_status_text TEXT,
                barista_order_reload_error_text TEXT,
                barista_status_updated_text TEXT,
                pickup_asap_text TEXT,
                order_type_pickup_label TEXT,
                order_type_delivery_label TEXT,
                order_status_new_label TEXT,
                order_status_in_progress_label TEXT,
                order_status_ready_label TEXT,
                order_status_en_route_label TEXT,
                order_status_completed_label TEXT,
                order_status_cancelled_label TEXT,
                order_contact_name_fallback TEXT,
                order_contact_phone_fallback TEXT,
                order_empty_items_text TEXT,
                order_promo_label TEXT,
                order_loyalty_label TEXT,
                order_bonus_spent_label TEXT,
                order_bonus_earned_label TEXT,
                order_note_label TEXT,
                order_delivery_address_label TEXT,
                order_delivery_comment_label TEXT,
                barista_action_take_text TEXT,
                barista_action_ready_text TEXT,
                barista_action_route_text TEXT,
                barista_action_done_text TEXT,
                barista_action_cancel_text TEXT,
                barista_order_card_text TEXT,
                barista_new_order_text TEXT,
                inactive_reminder_text TEXT
            )
            """
        )
    )
    for column_name, column_type in app_settings_columns.items():
        await conn.execute(
            text(f"ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
        )
    await conn.execute(
        text(
            """
            INSERT INTO app_settings (id)
            VALUES (1)
            ON CONFLICT (id) DO NOTHING
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE app_settings
            ADD COLUMN IF NOT EXISTS inactive_reminder_enabled BOOLEAN NOT NULL DEFAULT FALSE
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE app_settings
            ADD COLUMN IF NOT EXISTS inactive_reminder_days INTEGER NOT NULL DEFAULT 30
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE app_settings
            ADD COLUMN IF NOT EXISTS inactive_reminder_send_time VARCHAR(5) NOT NULL DEFAULT '12:00'
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE app_settings
            ADD COLUMN IF NOT EXISTS inactive_reminder_text TEXT
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE app_settings
            ADD COLUMN IF NOT EXISTS inactive_reminder_last_run_at TIMESTAMPTZ
            """
        )
    )

    await conn.execute(
        text(
            """
            UPDATE promo_codes
            SET discount_type = LOWER(discount_type)
            WHERE discount_type IS NOT NULL
            """
        )
    )

    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS image_url VARCHAR(1024)
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS category_id INTEGER
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS badge VARCHAR(60)
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS sku VARCHAR(64)
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS composition TEXT
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS volume_ml INTEGER
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS weight_g INTEGER
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS calories_kcal INTEGER
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS caffeine_mg INTEGER
            """
        )
    )

    if not await _column_exists(conn, "products", "product_type"):
        await conn.execute(
            text(
                """
                ALTER TABLE products
                ADD COLUMN product_type VARCHAR(80)
                """
            )
        )
        await conn.execute(
            text(
                """
                UPDATE products AS p
                SET product_type = c.slug
                FROM categories AS c
                WHERE p.category_id = c.id
                  AND p.product_type IS NULL
                """
            )
        )
        await conn.execute(
            text(
                """
                UPDATE products
                SET product_type = 'product'
                WHERE product_type IS NULL
                   OR BTRIM(product_type) = ''
                """
            )
        )
        await conn.execute(
            text(
                """
                ALTER TABLE products
                ALTER COLUMN product_type SET NOT NULL
                """
            )
        )
        await conn.execute(
            text(
                """
                ALTER TABLE products
                ALTER COLUMN product_type SET DEFAULT 'product'
                """
            )
        )
    else:
        await conn.execute(
            text(
                """
                UPDATE products
                SET product_type = 'product'
                WHERE product_type IS NULL
                   OR BTRIM(product_type) = ''
                """
            )
        )

    if not await _column_exists(conn, "products", "sort_order"):
        await conn.execute(
            text(
                """
                ALTER TABLE products
                ADD COLUMN sort_order INTEGER
                """
            )
        )
    await conn.execute(
        text(
            """
            UPDATE products
            SET sort_order = 100
            WHERE sort_order IS NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN sort_order SET NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN sort_order SET DEFAULT 100
            """
        )
    )

    if not await _column_exists(conn, "products", "has_sizes"):
        await conn.execute(
            text(
                """
                ALTER TABLE products
                ADD COLUMN has_sizes BOOLEAN
                """
            )
        )
        await conn.execute(
            text(
                """
                UPDATE products AS p
                SET has_sizes = CASE WHEN c.slug IN ('coffee', 'signature', 'tea') THEN TRUE ELSE FALSE END
                FROM categories AS c
                WHERE p.category_id = c.id
                  AND p.has_sizes IS NULL
                """
            )
        )

    if not await _column_exists(conn, "products", "has_addons"):
        await conn.execute(
            text(
                """
                ALTER TABLE products
                ADD COLUMN has_addons BOOLEAN
                """
            )
        )
        await conn.execute(
            text(
                """
                UPDATE products AS p
                SET has_addons = CASE WHEN c.slug IN ('coffee', 'signature') THEN TRUE ELSE FALSE END
                FROM categories AS c
                WHERE p.category_id = c.id
                  AND p.has_addons IS NULL
                """
            )
        )

    await conn.execute(
        text(
            """
            UPDATE products
            SET has_sizes = FALSE
            WHERE has_sizes IS NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN has_sizes SET NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN has_sizes SET DEFAULT FALSE
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE products
            SET has_addons = FALSE
            WHERE has_addons IS NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN has_addons SET NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN has_addons SET DEFAULT FALSE
            """
        )
    )

    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS size_options_json TEXT
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS addon_options_json TEXT
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE products
            SET size_options_json = :value
            WHERE COALESCE(BTRIM(size_options_json), '') = ''
              AND has_sizes IS TRUE
            """
        ),
        {"value": default_size_options_json},
    )
    await conn.execute(
        text(
            """
            UPDATE products
            SET addon_options_json = :value
            WHERE COALESCE(BTRIM(addon_options_json), '') = ''
              AND has_addons IS TRUE
            """
        ),
        {"value": default_addon_options_json},
    )
    await conn.execute(
        text(
            """
            UPDATE products
            SET size_options_json = '[]'
            WHERE size_options_json IS NULL
               OR BTRIM(size_options_json) = ''
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE products
            SET addon_options_json = '[]'
            WHERE addon_options_json IS NULL
               OR BTRIM(addon_options_json) = ''
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN size_options_json SET NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN size_options_json SET DEFAULT '[]'
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN addon_options_json SET NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE products
            ALTER COLUMN addon_options_json SET DEFAULT '[]'
            """
        )
    )

    if not await _column_exists(conn, "orders", "order_day"):
        await conn.execute(text("ALTER TABLE orders ADD COLUMN order_day DATE"))
        await conn.execute(
            text(
                """
                UPDATE orders
                SET order_day = COALESCE((created_at AT TIME ZONE :tz)::date, CURRENT_DATE)
                WHERE order_day IS NULL
                """
            ),
            {"tz": settings.APP_TIMEZONE},
        )
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN order_day SET NOT NULL"))
        await conn.execute(text("ALTER TABLE orders ALTER COLUMN order_day SET DEFAULT CURRENT_DATE"))

    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS branch_id INTEGER
            """
        )
    )

    await conn.execute(
        text(
            """
            UPDATE orders
            SET order_type = LOWER(order_type)
            WHERE order_type IS NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE orders
            SET status = LOWER(status)
            WHERE status IS NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS order_type VARCHAR(20) NOT NULL DEFAULT 'pickup'
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS consumption_place VARCHAR(20) NOT NULL DEFAULT 'takeaway'
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE orders
            SET consumption_place = LOWER(consumption_place)
            WHERE consumption_place IS NOT NULL
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS contact_name VARCHAR(255)
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(40)
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS delivery_address VARCHAR(255)
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS delivery_comment TEXT
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS scheduled_for TIMESTAMPTZ
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS pickup_label VARCHAR(80)
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS delivery_fee_cents INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS promo_discount_cents INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS bonus_spent_cents INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS bonus_earned_cents INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS bonus_accrued BOOLEAN NOT NULL DEFAULT FALSE
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS bonus_refunded BOOLEAN NOT NULL DEFAULT FALSE
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS loyalty_discount_cents INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS loyalty_paid_coffee_count INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS loyalty_free_coffee_count INTEGER NOT NULL DEFAULT 0
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS loyalty_reserved BOOLEAN NOT NULL DEFAULT FALSE
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS rating INTEGER
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS feedback_text TEXT
            """
        )
    )

    await conn.execute(text("ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_order_number_key"))
    await conn.execute(text("DROP INDEX IF EXISTS ix_orders_order_number"))
    await conn.execute(
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_day_number
            ON orders (order_day, order_number)
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_orders_day_number
            ON orders (order_day, order_number)
            """
        )
    )
