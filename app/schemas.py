from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models import ConsumptionPlace, OrderStatus, OrderType


class SizeOptionOut(BaseModel):
    code: str
    name: str
    volume_label: str
    price_cents: int

    model_config = ConfigDict(from_attributes=True)


class AddonOptionOut(BaseModel):
    code: str
    name: str
    price_cents: int

    model_config = ConfigDict(from_attributes=True)


class CategoryOut(BaseModel):
    id: int
    slug: str
    name: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class BannerOut(BaseModel):
    id: int
    title: str
    subtitle: str | None
    description: str | None
    image_url: str | None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ProductOut(BaseModel):
    id: int
    category_id: int | None
    category_slug: str | None = None
    product_type: str
    name: str
    description: str | None
    composition: str | None
    image_url: str | None
    badge: str | None
    calories_kcal: int | None
    price_cents: int
    supports_sizes: bool
    supports_addons: bool
    sort_order: int
    size_options: list[SizeOptionOut] = Field(default_factory=list)
    addon_options: list[AddonOptionOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MeOut(BaseModel):
    telegram_id: int
    username: str | None
    full_name: str | None
    phone: str | None
    bonus_balance: int
    loyalty_category_slug: str
    loyalty_category_slugs: list[str] = Field(default_factory=list)
    loyalty_progress: int
    loyalty_goal: int
    loyalty_rewards_available: int
    bonus_enabled: bool
    bonus_redeem_enabled: bool
    bonus_redeem_max_percent: int = 100
    is_phone_verified: bool


class BootstrapOut(BaseModel):
    me: MeOut
    banners: list[BannerOut]
    categories: list[CategoryOut]
    products: list[ProductOut]


class TelegramAuthIn(BaseModel):
    init_data: str | None = None


class UpdateProfileIn(BaseModel):
    full_name: str | None = Field(default=None, max_length=80)


class OrderItemIn(BaseModel):
    product_id: int
    qty: int = Field(ge=1, le=50)
    size_code: str | None = Field(default=None, max_length=64)
    addon_codes: list[str] = Field(default_factory=list, max_length=10)


class CreateOrderIn(BaseModel):
    order_type: OrderType = OrderType.PICKUP
    consumption_place: ConsumptionPlace = ConsumptionPlace.TAKEAWAY
    pickup_time: str | None = Field(default=None, max_length=80)
    use_bonus_cents: int = Field(default=0, ge=0)
    items: list[OrderItemIn]
    promo_code: str | None = Field(default=None, max_length=50)
    note: str | None = Field(default=None, max_length=500)


class OrderItemOut(BaseModel):
    product_id: int
    qty: int
    price_cents: int
    name_snapshot: str

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    order_number: str
    order_day: date | None = None
    order_type: OrderType
    consumption_place: ConsumptionPlace
    status: OrderStatus
    total_cents: int
    discount_cents: int
    final_cents: int
    delivery_fee_cents: int
    promo_discount_cents: int
    bonus_spent_cents: int
    bonus_earned_cents: int
    loyalty_discount_cents: int
    loyalty_paid_coffee_count: int
    loyalty_free_coffee_count: int
    contact_name: str | None
    contact_phone: str | None
    pickup_eta_minutes: int
    pickup_label: str | None
    note: str | None
    delivery_address: str | None
    delivery_comment: str | None
    scheduled_for: datetime | None
    created_at: datetime
    items: list[OrderItemOut]

    model_config = ConfigDict(from_attributes=True)


class AdminLoginIn(BaseModel):
    secret: str = Field(min_length=3, max_length=255)


class AdminCategoryIn(BaseModel):
    slug: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    sort_order: int = Field(default=100, ge=0, le=10000)
    is_active: bool = True


class AdminCategoryOut(BaseModel):
    id: int
    slug: str
    name: str
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AdminSizeOptionIn(BaseModel):
    code: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=80)
    volume_label: str = Field(min_length=1, max_length=40)
    price_cents: int = Field(ge=0, le=1000000)


class AdminAddonOptionIn(BaseModel):
    code: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=80)
    price_cents: int = Field(default=0, ge=0, le=1000000)


class AdminBannerIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    subtitle: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    image_url: str | None = Field(default=None, max_length=1024)
    sort_order: int = Field(default=100, ge=0, le=10000)
    is_active: bool = True


class AdminBannerOut(BaseModel):
    id: int
    title: str
    subtitle: str | None
    description: str | None
    image_url: str | None
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AdminBaristaIn(BaseModel):
    telegram_id: int | None = Field(default=None, ge=1)
    username: str | None = Field(default=None, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    is_barista: bool = True


class AdminBaristaOut(BaseModel):
    id: int
    telegram_id: int | None
    username: str | None
    full_name: str | None
    is_barista: bool
    is_pending: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminBaristaShiftIn(BaseModel):
    user_id: int = Field(ge=1)
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    note: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class AdminBaristaShiftOut(BaseModel):
    id: int
    user_id: int
    barista_name: str
    barista_username: str | None
    barista_telegram_id: int | None
    barista_is_pending: bool = False
    weekday: int
    start_time: time
    end_time: time
    note: str | None
    is_active: bool
    created_at: datetime


class AdminProductIn(BaseModel):
    category_id: int | None = None
    product_type: str = Field(default="product", min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    composition: str | None = Field(default=None, max_length=2000)
    image_url: str | None = Field(default=None, max_length=1024)
    badge: str | None = Field(default=None, max_length=60)
    calories_kcal: int | None = Field(default=None, ge=0, le=10000)
    sort_order: int = Field(default=100, ge=0, le=10000)
    is_active: bool = True
    size_options: list[AdminSizeOptionIn] = Field(default_factory=list)
    addon_options: list[AdminAddonOptionIn] = Field(default_factory=list)


class AdminProductOut(BaseModel):
    id: int
    category_id: int | None
    category_slug: str | None = None
    category_name: str | None = None
    product_type: str
    name: str
    description: str | None
    composition: str | None
    image_url: str | None
    badge: str | None
    calories_kcal: int | None
    price_cents: int
    sort_order: int
    has_sizes: bool
    has_addons: bool
    is_active: bool
    size_options: list[SizeOptionOut] = Field(default_factory=list)
    addon_options: list[AddonOptionOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AdminProgramsSettingsIn(BaseModel):
    classic_category_slug: str | None = Field(default=None, max_length=80)
    classic_category_slugs: list[str] = Field(default_factory=list, max_length=20)
    paid_items_per_reward: int = Field(ge=1, le=100)
    bonus_enabled: bool = True
    bonus_earn_percent: int = Field(default=5, ge=0, le=100)
    bonus_redeem_enabled: bool = True
    bonus_redeem_max_percent: int = Field(default=100, ge=0, le=100)


class AdminProgramsSettingsOut(BaseModel):
    classic_category_slug: str
    classic_category_slugs: list[str] = Field(default_factory=list)
    paid_items_per_reward: int
    bonus_enabled: bool
    bonus_earn_percent: int
    bonus_redeem_enabled: bool
    bonus_redeem_max_percent: int


class AdminAppSettingsIn(BaseModel):
    miniapp_button_text: str = Field(max_length=120)
    customer_start_text: str = Field(max_length=4000)
    customer_app_text: str = Field(max_length=4000)
    customer_help_text: str = Field(max_length=4000)
    customer_contact_request_text: str = Field(max_length=4000)
    customer_phone_error_text: str = Field(max_length=4000)
    customer_phone_saved_text: str = Field(max_length=4000)
    customer_order_created_text: str = Field(max_length=4000)
    customer_status_in_progress_text: str = Field(max_length=4000)
    customer_status_ready_text: str = Field(max_length=4000)
    customer_status_en_route_text: str = Field(max_length=4000)
    customer_status_completed_text: str = Field(max_length=4000)
    customer_status_cancelled_text: str = Field(max_length=4000)
    barista_start_text: str = Field(max_length=4000)
    barista_login_invalid_text: str = Field(max_length=4000)
    barista_login_success_text: str = Field(max_length=4000)
    barista_logout_text: str = Field(max_length=4000)
    barista_access_denied_text: str = Field(max_length=4000)
    barista_queue_empty_text: str = Field(max_length=4000)
    barista_queue_summary_text: str = Field(max_length=4000)
    barista_order_usage_text: str = Field(max_length=4000)
    barista_order_not_found_text: str = Field(max_length=4000)
    barista_today_empty_text: str = Field(max_length=4000)
    barista_today_summary_text: str = Field(max_length=4000)
    barista_user_not_found_text: str = Field(max_length=4000)
    barista_invalid_order_id_text: str = Field(max_length=4000)
    barista_unknown_action_text: str = Field(max_length=4000)
    barista_order_closed_text: str = Field(max_length=4000)
    barista_delivery_only_status_text: str = Field(max_length=4000)
    barista_order_reload_error_text: str = Field(max_length=4000)
    barista_status_updated_text: str = Field(max_length=4000)
    pickup_asap_text: str = Field(max_length=255)
    order_type_pickup_label: str = Field(max_length=255)
    order_type_delivery_label: str = Field(max_length=255)
    order_status_new_label: str = Field(max_length=255)
    order_status_in_progress_label: str = Field(max_length=255)
    order_status_ready_label: str = Field(max_length=255)
    order_status_en_route_label: str = Field(max_length=255)
    order_status_completed_label: str = Field(max_length=255)
    order_status_cancelled_label: str = Field(max_length=255)
    order_contact_name_fallback: str = Field(max_length=255)
    order_contact_phone_fallback: str = Field(max_length=255)
    order_empty_items_text: str = Field(max_length=255)
    order_promo_label: str = Field(max_length=255)
    order_loyalty_label: str = Field(max_length=255)
    order_bonus_spent_label: str = Field(max_length=255)
    order_bonus_earned_label: str = Field(max_length=255)
    order_note_label: str = Field(max_length=255)
    order_delivery_address_label: str = Field(max_length=255)
    order_delivery_comment_label: str = Field(max_length=255)
    barista_action_take_text: str = Field(max_length=255)
    barista_action_ready_text: str = Field(max_length=255)
    barista_action_route_text: str = Field(max_length=255)
    barista_action_done_text: str = Field(max_length=255)
    barista_action_cancel_text: str = Field(max_length=255)
    barista_order_card_text: str = Field(max_length=8000)
    barista_new_order_text: str = Field(max_length=8000)


class AdminAppSettingsOut(AdminAppSettingsIn):
    pass


class AdminReminderSettingsIn(BaseModel):
    inactive_reminder_enabled: bool = False
    inactive_reminder_days: int = Field(default=30, ge=1, le=3650)
    inactive_reminder_send_time: str = Field(default="12:00", min_length=5, max_length=5)
    inactive_reminder_text: str = Field(default="", max_length=4000)


class AdminReminderSettingsOut(AdminReminderSettingsIn):
    inactive_reminder_last_run_at: datetime | None = None


class AdminBootstrapOut(BaseModel):
    banners: list[AdminBannerOut]
    categories: list[AdminCategoryOut]
    baristas: list[AdminBaristaOut]
    barista_shifts: list[AdminBaristaShiftOut]
    products: list[AdminProductOut]
    program_settings: AdminProgramsSettingsOut
    app_settings: AdminAppSettingsOut
    reminder_settings: AdminReminderSettingsOut


class AdminAnalyticsKpiOut(BaseModel):
    total_orders: int
    completed_orders: int
    cancelled_orders: int
    completion_rate: float
    gross_revenue_cents: int
    net_revenue_cents: int
    average_order_value_cents: int
    unique_customers: int
    repeat_customers: int
    bonus_spent_cents: int
    bonus_earned_cents: int
    promo_discount_cents: int
    loyalty_discount_cents: int


class AdminAnalyticsTopItemOut(BaseModel):
    key: str
    name: str
    qty: int
    revenue_cents: int


class AdminAnalyticsPromoOut(BaseModel):
    code: str
    uses: int
    discount_cents: int


class AdminAnalyticsStatusOut(BaseModel):
    status: str
    qty: int


class AdminAnalyticsDailyOut(BaseModel):
    day: date
    orders: int
    revenue_cents: int


class AdminAnalyticsOrderOut(BaseModel):
    id: int
    order_number: str
    created_at: datetime
    status: str
    consumption_place: ConsumptionPlace
    customer_name: str | None
    customer_phone: str | None
    promo_code: str | None
    total_cents: int
    discount_cents: int
    final_cents: int
    bonus_spent_cents: int
    bonus_earned_cents: int
    loyalty_discount_cents: int


class AdminAnalyticsItemOut(BaseModel):
    order_id: int
    order_number: str
    created_at: datetime
    status: str
    consumption_place: ConsumptionPlace
    customer_name: str | None
    customer_phone: str | None
    promo_code: str | None
    product_id: int
    product_name: str
    category_slug: str | None
    qty: int
    unit_price_cents: int
    line_total_cents: int
    total_cents: int
    discount_cents: int
    final_cents: int
    bonus_spent_cents: int
    bonus_earned_cents: int
    loyalty_discount_cents: int


class AdminAnalyticsOut(BaseModel):
    date_from: date
    date_to: date
    kpis: AdminAnalyticsKpiOut
    top_products: list[AdminAnalyticsTopItemOut] = Field(default_factory=list)
    top_categories: list[AdminAnalyticsTopItemOut] = Field(default_factory=list)
    promo_usage: list[AdminAnalyticsPromoOut] = Field(default_factory=list)
    status_breakdown: list[AdminAnalyticsStatusOut] = Field(default_factory=list)
    daily_revenue: list[AdminAnalyticsDailyOut] = Field(default_factory=list)
    orders: list[AdminAnalyticsOrderOut] = Field(default_factory=list)
    items: list[AdminAnalyticsItemOut] = Field(default_factory=list)


class AdminUploadOut(BaseModel):
    url: str


AdminProductIn.model_rebuild()
