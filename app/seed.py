from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Banner, Branch, Category, Product, PromoCode, PromoDiscountType
from app.services.menu import default_addon_option_payloads, default_size_option_payloads, serialize_option_payloads, supports_addons, supports_sizes

BRANCHES = [
    {
        "city": "Минск",
        "name": "Coffee Flow Немига",
        "address": "ул. Немига, 12",
        "phone": "+375291110011",
        "hours_text": "Ежедневно 08:00-22:00",
        "image_url": "/static/images/branch-nemiga.svg",
        "pickup_available": True,
        "delivery_available": False,
        "sort_order": 10,
    },
    {
        "city": "Минск",
        "name": "Coffee Flow Восток",
        "address": "пр-т Независимости, 168/3",
        "phone": "+375291110022",
        "hours_text": "Ежедневно 08:00-21:30",
        "image_url": "/static/images/branch-vostok.svg",
        "pickup_available": True,
        "delivery_available": False,
        "sort_order": 20,
    },
    {
        "city": "Гродно",
        "name": "Coffee Flow Центр",
        "address": "ул. Советская, 18",
        "phone": "+375291110033",
        "hours_text": "Ежедневно 09:00-22:00",
        "image_url": "/static/images/branch-grodno.svg",
        "pickup_available": True,
        "delivery_available": False,
        "sort_order": 30,
    },
]

CATEGORIES = [
    {"slug": "coffee", "name": "Кофе", "sort_order": 10},
    {"slug": "signature", "name": "Авторские", "sort_order": 20},
    {"slug": "tea", "name": "Чай и какао", "sort_order": 30},
    {"slug": "desserts", "name": "Десерты и перекус", "sort_order": 40},
]

BANNERS = [
    {
        "title": "Капучино недели",
        "subtitle": "-20% по промокоду CAP20",
        "description": "Сделайте предзаказ и заберите кофе без очереди.",
        "image_url": "/static/images/banner-week.svg",
        "sort_order": 10,
    },
    {
        "title": "Утренний сет",
        "subtitle": "Круассан + латте",
        "description": "Быстрый завтрак для самовывоза к нужному времени.",
        "image_url": "/static/images/banner-set.svg",
        "sort_order": 20,
    },
]

PRODUCTS = [
    {
        "category_slug": "coffee",
        "name": "Эспрессо",
        "description": "Плотный шот с шоколадным послевкусием",
        "price_cents": 320,
        "image_url": "/static/images/espresso.svg",
        "badge": "Хит",
    },
    {
        "category_slug": "coffee",
        "name": "Американо",
        "description": "Чистый вкус арабики, можно взять покрепче",
        "price_cents": 360,
        "image_url": "/static/images/americano.svg",
        "badge": None,
    },
    {
        "category_slug": "coffee",
        "name": "Капучино",
        "description": "Мягкая молочная текстура и стабильная пена",
        "price_cents": 430,
        "image_url": "/static/images/cappuccino.svg",
        "badge": "Популярно",
    },
    {
        "category_slug": "coffee",
        "name": "Латте",
        "description": "Мягкий сливочный вкус на каждый день",
        "price_cents": 470,
        "image_url": "/static/images/latte.svg",
        "badge": None,
    },
    {
        "category_slug": "coffee",
        "name": "Флэт уайт",
        "description": "Насыщенный кофе на двойном эспрессо с микропеной",
        "price_cents": 520,
        "image_url": "/static/images/flatwhite.svg",
        "badge": "Бодрость",
    },
    {
        "category_slug": "signature",
        "name": "Фисташковый латте",
        "description": "Авторский напиток с кремовой фисташкой",
        "price_cents": 560,
        "image_url": "/static/images/latte.svg",
        "badge": "Новинка",
    },
    {
        "category_slug": "signature",
        "name": "Раф соленая карамель",
        "description": "Сливочный напиток с глубоким вкусом карамели",
        "price_cents": 590,
        "image_url": "/static/images/latte.svg",
        "badge": "Хит",
    },
    {
        "category_slug": "tea",
        "name": "Матча латте",
        "description": "Японская матча с молоком и легкой сладостью",
        "price_cents": 540,
        "image_url": "/static/images/flatwhite.svg",
        "badge": "Новинка",
    },
    {
        "category_slug": "tea",
        "name": "Цитрусовый чай",
        "description": "Чай с апельсином, лаймом и медом",
        "price_cents": 430,
        "image_url": "/static/images/americano.svg",
        "badge": None,
    },
    {
        "category_slug": "desserts",
        "name": "Круассан",
        "description": "Свежий масляный круассан, подаем теплым",
        "price_cents": 310,
        "image_url": "/static/images/croissant.svg",
        "badge": None,
    },
    {
        "category_slug": "desserts",
        "name": "Чизкейк",
        "description": "Нежный десерт для пары с кофе",
        "price_cents": 420,
        "image_url": "/static/images/cheesecake.svg",
        "badge": "Сет",
    },
    {
        "category_slug": "desserts",
        "name": "Сэндвич с индейкой",
        "description": "Сытный перекус с индейкой и сливочным соусом",
        "price_cents": 610,
        "image_url": "/static/images/croissant.svg",
        "badge": "Ланч",
    },
]


async def seed_data(session: AsyncSession) -> None:
    branch_exists = await session.scalar(select(Branch.id).limit(1))
    if branch_exists is None:
        session.add_all(Branch(**item) for item in BRANCHES)

    category_exists = await session.scalar(select(Category.id).limit(1))
    if category_exists is None:
        session.add_all(Category(**item) for item in CATEGORIES)

    await session.flush()

    category_result = await session.execute(select(Category))
    category_map = {category.slug: category for category in category_result.scalars().all()}

    banner_exists = await session.scalar(select(Banner.id).limit(1))
    if banner_exists is None:
        session.add_all(Banner(**item) for item in BANNERS)

    product_exists = await session.scalar(select(Product.id).limit(1))
    if product_exists is None:
        for index, item in enumerate(PRODUCTS, start=1):
            category_slug = item["category_slug"]
            category = category_map[category_slug]
            session.add(
                Product(
                    category_id=category.id,
                    product_type=category_slug,
                    name=item["name"],
                    description=item["description"],
                    composition=item.get("composition"),
                    price_cents=item["price_cents"],
                    image_url=item["image_url"],
                    badge=item["badge"],
                    volume_ml=item.get("volume_ml"),
                    weight_g=item.get("weight_g"),
                    calories_kcal=item.get("calories_kcal"),
                    sort_order=index * 10,
                    has_sizes=supports_sizes(
                        default_size_option_payloads(
                            base_price_cents=item["price_cents"],
                            product_type=category_slug,
                        )
                    ),
                    has_addons=supports_addons(default_addon_option_payloads() if category_slug in {"coffee", "signature"} else []),
                    size_options_json=serialize_option_payloads(
                        default_size_option_payloads(
                            base_price_cents=item["price_cents"],
                            product_type=category_slug,
                        )
                    ),
                    addon_options_json=serialize_option_payloads(
                        default_addon_option_payloads() if category_slug in {"coffee", "signature"} else []
                    ),
                )
            )

    promo = await session.scalar(select(PromoCode).where(PromoCode.code == "WELCOME10"))
    if promo is None:
        session.add(
            PromoCode(
                code="WELCOME10",
                discount_type=PromoDiscountType.PERCENT,
                discount_value=10,
                max_uses=10000,
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            )
        )

    promo_cap = await session.scalar(select(PromoCode).where(PromoCode.code == "CAP20"))
    if promo_cap is None:
        session.add(
            PromoCode(
                code="CAP20",
                discount_type=PromoDiscountType.PERCENT,
                discount_value=20,
                max_uses=300,
                expires_at=datetime.now(timezone.utc) + timedelta(days=60),
            )
        )

    await session.commit()
