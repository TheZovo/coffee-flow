from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class PromoDiscountType(str, Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class OrderType(str, Enum):
    PICKUP = "pickup"
    DELIVERY = "delivery"


class ConsumptionPlace(str, Enum):
    TAKEAWAY = "takeaway"
    DINE_IN = "dine_in"


class OrderStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    EN_ROUTE = "en_route"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(40))
    bonus_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loyalty_paid_coffee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loyalty_free_coffee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_barista: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    inactive_reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    orders: Mapped[list[Order]] = relationship(back_populates="user")
    barista_shifts: Mapped[list[BaristaShift]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    hours_text: Mapped[str | None] = mapped_column(String(255))
    image_url: Mapped[str | None] = mapped_column(String(1024))
    pickup_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    delivery_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    orders: Mapped[list[Order]] = relationship(back_populates="branch")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products: Mapped[list[Product]] = relationship(back_populates="category")


class Banner(Base):
    __tablename__ = "banners"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text())
    image_url: Mapped[str | None] = mapped_column(String(1024))
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class LoyaltySettings(Base):
    __tablename__ = "loyalty_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    classic_category_slug: Mapped[str] = mapped_column(String(80), nullable=False, default="coffee")
    classic_category_slugs: Mapped[str] = mapped_column(Text(), nullable=False, default="coffee")
    paid_items_per_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    bonus_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    bonus_earn_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    bonus_redeem_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    bonus_redeem_max_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=100)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    miniapp_button_text: Mapped[str | None] = mapped_column(Text())
    customer_start_text: Mapped[str | None] = mapped_column(Text())
    customer_app_text: Mapped[str | None] = mapped_column(Text())
    customer_help_text: Mapped[str | None] = mapped_column(Text())
    customer_contact_request_text: Mapped[str | None] = mapped_column(Text())
    customer_phone_error_text: Mapped[str | None] = mapped_column(Text())
    customer_phone_saved_text: Mapped[str | None] = mapped_column(Text())
    customer_order_created_text: Mapped[str | None] = mapped_column(Text())
    customer_status_in_progress_text: Mapped[str | None] = mapped_column(Text())
    customer_status_ready_text: Mapped[str | None] = mapped_column(Text())
    customer_status_en_route_text: Mapped[str | None] = mapped_column(Text())
    customer_status_completed_text: Mapped[str | None] = mapped_column(Text())
    customer_status_cancelled_text: Mapped[str | None] = mapped_column(Text())
    barista_start_text: Mapped[str | None] = mapped_column(Text())
    barista_login_invalid_text: Mapped[str | None] = mapped_column(Text())
    barista_login_success_text: Mapped[str | None] = mapped_column(Text())
    barista_logout_text: Mapped[str | None] = mapped_column(Text())
    barista_access_denied_text: Mapped[str | None] = mapped_column(Text())
    barista_queue_empty_text: Mapped[str | None] = mapped_column(Text())
    barista_queue_summary_text: Mapped[str | None] = mapped_column(Text())
    barista_order_usage_text: Mapped[str | None] = mapped_column(Text())
    barista_order_not_found_text: Mapped[str | None] = mapped_column(Text())
    barista_today_empty_text: Mapped[str | None] = mapped_column(Text())
    barista_today_summary_text: Mapped[str | None] = mapped_column(Text())
    barista_user_not_found_text: Mapped[str | None] = mapped_column(Text())
    barista_invalid_order_id_text: Mapped[str | None] = mapped_column(Text())
    barista_unknown_action_text: Mapped[str | None] = mapped_column(Text())
    barista_order_closed_text: Mapped[str | None] = mapped_column(Text())
    barista_delivery_only_status_text: Mapped[str | None] = mapped_column(Text())
    barista_order_reload_error_text: Mapped[str | None] = mapped_column(Text())
    barista_status_updated_text: Mapped[str | None] = mapped_column(Text())
    pickup_asap_text: Mapped[str | None] = mapped_column(Text())
    order_type_pickup_label: Mapped[str | None] = mapped_column(Text())
    order_type_delivery_label: Mapped[str | None] = mapped_column(Text())
    order_status_new_label: Mapped[str | None] = mapped_column(Text())
    order_status_in_progress_label: Mapped[str | None] = mapped_column(Text())
    order_status_ready_label: Mapped[str | None] = mapped_column(Text())
    order_status_en_route_label: Mapped[str | None] = mapped_column(Text())
    order_status_completed_label: Mapped[str | None] = mapped_column(Text())
    order_status_cancelled_label: Mapped[str | None] = mapped_column(Text())
    order_contact_name_fallback: Mapped[str | None] = mapped_column(Text())
    order_contact_phone_fallback: Mapped[str | None] = mapped_column(Text())
    order_empty_items_text: Mapped[str | None] = mapped_column(Text())
    order_promo_label: Mapped[str | None] = mapped_column(Text())
    order_loyalty_label: Mapped[str | None] = mapped_column(Text())
    order_bonus_spent_label: Mapped[str | None] = mapped_column(Text())
    order_bonus_earned_label: Mapped[str | None] = mapped_column(Text())
    order_note_label: Mapped[str | None] = mapped_column(Text())
    order_delivery_address_label: Mapped[str | None] = mapped_column(Text())
    order_delivery_comment_label: Mapped[str | None] = mapped_column(Text())
    barista_action_take_text: Mapped[str | None] = mapped_column(Text())
    barista_action_ready_text: Mapped[str | None] = mapped_column(Text())
    barista_action_route_text: Mapped[str | None] = mapped_column(Text())
    barista_action_done_text: Mapped[str | None] = mapped_column(Text())
    barista_action_cancel_text: Mapped[str | None] = mapped_column(Text())
    barista_order_card_text: Mapped[str | None] = mapped_column(Text())
    barista_new_order_text: Mapped[str | None] = mapped_column(Text())
    inactive_reminder_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    inactive_reminder_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    inactive_reminder_send_time: Mapped[str] = mapped_column(String(5), nullable=False, default="12:00")
    inactive_reminder_text: Mapped[str | None] = mapped_column(Text())
    inactive_reminder_last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BaristaShift(Base):
    __tablename__ = "barista_shifts"
    __table_args__ = (
        Index("ix_barista_shifts_user_weekday_time", "user_id", "weekday", "start_time", "end_time"),
        Index("ix_barista_shifts_active_weekday_time", "is_active", "weekday", "start_time", "end_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time(), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="barista_shifts")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    sku: Mapped[str | None] = mapped_column(String(64))
    product_type: Mapped[str] = mapped_column(String(80), default="product", nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    composition: Mapped[str | None] = mapped_column(Text())
    image_url: Mapped[str | None] = mapped_column(String(1024))
    badge: Mapped[str | None] = mapped_column(String(60))
    volume_ml: Mapped[int | None] = mapped_column(Integer)
    weight_g: Mapped[int | None] = mapped_column(Integer)
    calories_kcal: Mapped[int | None] = mapped_column(Integer)
    caffeine_mg: Mapped[int | None] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    has_sizes: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_addons: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    size_options_json: Mapped[str] = mapped_column(Text(), default="[]", nullable=False)
    addon_options_json: Mapped[str] = mapped_column(Text(), default="[]", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    category: Mapped[Category | None] = relationship(back_populates="products")
    order_items: Mapped[list[OrderItem]] = relationship(back_populates="product")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    discount_type: Mapped[PromoDiscountType] = mapped_column(
        SQLEnum(PromoDiscountType, native_enum=False, length=20, values_callable=_enum_values),
        nullable=False,
    )
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    orders: Mapped[list[Order]] = relationship(back_populates="promo_code")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_day", "order_number", name="uq_orders_day_number"),
        Index("ix_orders_day_number", "order_day", "order_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_day: Mapped[date] = mapped_column(
        Date(),
        nullable=False,
        server_default=func.current_date(),
    )
    order_number: Mapped[str] = mapped_column(String(16), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    promo_code_id: Mapped[int | None] = mapped_column(ForeignKey("promo_codes.id"))

    order_type: Mapped[OrderType] = mapped_column(
        SQLEnum(OrderType, native_enum=False, length=20, values_callable=_enum_values),
        default=OrderType.PICKUP,
        nullable=False,
    )
    consumption_place: Mapped[ConsumptionPlace] = mapped_column(
        SQLEnum(ConsumptionPlace, native_enum=False, length=20, values_callable=_enum_values),
        default=ConsumptionPlace.TAKEAWAY,
        nullable=False,
    )
    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(40))
    delivery_address: Mapped[str | None] = mapped_column(String(255))
    delivery_comment: Mapped[str | None] = mapped_column(Text())
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_label: Mapped[str | None] = mapped_column(String(80))

    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_fee_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    promo_discount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_spent_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_earned_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_accrued: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bonus_refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    loyalty_discount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loyalty_paid_coffee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loyalty_free_coffee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loyalty_reserved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    customer_last_message_id: Mapped[int | None] = mapped_column(BigInteger)
    customer_last_message_status: Mapped[str | None] = mapped_column(String(32))

    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, native_enum=False, length=20, values_callable=_enum_values),
        default=OrderStatus.NEW,
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text())
    pickup_eta_minutes: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer)
    feedback_text: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="orders")
    branch: Mapped[Branch | None] = relationship(back_populates="orders")
    promo_code: Mapped[PromoCode | None] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="order_items")
