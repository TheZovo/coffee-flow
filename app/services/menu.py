from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

DRINK_PRODUCT_TYPES = {"coffee", "signature", "tea", "drink", "beverage"}
DEFAULT_DRINK_SIZE_TEMPLATES = [
    ("small", "Маленький", "250 мл", 0),
    ("medium", "Средний", "350 мл", 70),
    ("large", "Большой", "450 мл", 140),
]
STANDARD_SIZE_NAME = "Стандарт"
STANDARD_SIZE_LABEL = "1 шт"


@dataclass(frozen=True)
class SizeOption:
    code: str
    name: str
    volume_label: str
    price_cents: int


@dataclass(frozen=True)
class AddonOption:
    code: str
    name: str
    price_cents: int


DEFAULT_ADDON_OPTIONS = [
    AddonOption(code="vanilla", name="Ваниль", price_cents=70),
    AddonOption(code="caramel", name="Карамель", price_cents=70),
    AddonOption(code="hazelnut", name="Лесной орех", price_cents=70),
    AddonOption(code="cinnamon", name="Корица", price_cents=40),
    AddonOption(code="oat", name="Овсяное молоко", price_cents=90),
]


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _slugify(value: str, fallback_prefix: str, index: int) -> str:
    normalized = re.sub(r"\s+", "-", (value or "").strip().lower())
    normalized = re.sub(r"[^\w-]+", "", normalized, flags=re.UNICODE)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        normalized = f"{fallback_prefix}-{index}"
    return normalized[:40]


def _ensure_unique_code(base_code: str, seen: set[str]) -> str:
    if base_code not in seen:
        seen.add(base_code)
        return base_code

    suffix = 2
    while True:
        suffix_code = f"{base_code[:34]}-{suffix}"
        if suffix_code not in seen:
            seen.add(suffix_code)
            return suffix_code
        suffix += 1


def _normalized_product_type(product_type: str | None) -> str:
    return (product_type or "").strip().lower()


def default_drink_size_option_payloads(base_price_cents: int) -> list[dict]:
    base_price_cents = max(0, _safe_int(base_price_cents))
    return [
        {
            "code": code,
            "name": name,
            "volume_label": volume_label,
            "price_cents": base_price_cents + price_step,
        }
        for code, name, volume_label, price_step in DEFAULT_DRINK_SIZE_TEMPLATES
    ]


def default_standard_size_option_payload(base_price_cents: int) -> list[dict]:
    return [
        {
            "code": "standard",
            "name": STANDARD_SIZE_NAME,
            "volume_label": STANDARD_SIZE_LABEL,
            "price_cents": max(0, _safe_int(base_price_cents)),
        }
    ]


def default_size_option_payloads(base_price_cents: int = 0, product_type: str | None = None) -> list[dict]:
    if _normalized_product_type(product_type) in DRINK_PRODUCT_TYPES:
        return default_drink_size_option_payloads(base_price_cents)
    return default_standard_size_option_payload(base_price_cents)


def default_addon_option_payloads() -> list[dict]:
    return [asdict(item) for item in DEFAULT_ADDON_OPTIONS]


def serialize_option_payloads(items: list[dict]) -> str:
    return json.dumps(items, ensure_ascii=False, separators=(",", ":"))


def _normalize_size_item(
    item: object,
    index: int,
    seen_codes: set[str],
    base_price_cents: int = 0,
) -> dict | None:
    if not isinstance(item, dict):
        return None

    name = str(item.get("name") or "").strip()
    volume_label = str(item.get("volume_label") or "").strip()
    if not name or not volume_label:
        return None

    code = str(item.get("code") or "").strip().lower()
    base_code = code or _slugify(name, "size", index)
    raw_price = item.get("price_cents")
    if raw_price is None and "price_delta_cents" in item:
        raw_price = max(0, _safe_int(base_price_cents)) + _safe_int(item.get("price_delta_cents"))

    return {
        "code": _ensure_unique_code(base_code, seen_codes),
        "name": name[:80],
        "volume_label": volume_label[:40],
        "price_cents": max(0, _safe_int(raw_price)),
    }


def _normalize_addon_item(item: object, index: int, seen_codes: set[str]) -> dict | None:
    if not isinstance(item, dict):
        return None

    name = str(item.get("name") or "").strip()
    if not name:
        return None

    code = str(item.get("code") or "").strip().lower()
    base_code = code or _slugify(name, "addon", index)
    return {
        "code": _ensure_unique_code(base_code, seen_codes),
        "name": name[:80],
        "price_cents": max(0, _safe_int(item.get("price_cents"), 0)),
    }


def normalize_size_options(items: list[object] | None, base_price_cents: int = 0) -> list[dict]:
    result: list[dict] = []
    seen_codes: set[str] = set()
    for index, item in enumerate(items or [], start=1):
        normalized = _normalize_size_item(item, index, seen_codes, base_price_cents=base_price_cents)
        if normalized is not None:
            result.append(normalized)
    return result


def normalize_addon_options(items: list[object] | None) -> list[dict]:
    result: list[dict] = []
    seen_codes: set[str] = set()
    for index, item in enumerate(items or [], start=1):
        normalized = _normalize_addon_item(item, index, seen_codes)
        if normalized is not None:
            result.append(normalized)
    return result


def _parse_items(raw: str | list[dict] | None) -> list[dict]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if not raw.strip():
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def parse_size_options(raw: str | list[dict] | None, base_price_cents: int = 0) -> list[SizeOption]:
    result: list[SizeOption] = []
    for item in normalize_size_options(_parse_items(raw), base_price_cents=base_price_cents):
        result.append(
            SizeOption(
                code=item["code"],
                name=item["name"],
                volume_label=item["volume_label"],
                price_cents=item["price_cents"],
            )
        )
    return result


def parse_addon_options(raw: str | list[dict] | None) -> list[AddonOption]:
    result: list[AddonOption] = []
    for item in _parse_items(raw):
        code = str(item.get("code") or "").strip()
        name = str(item.get("name") or "").strip()
        if not code or not name:
            continue
        result.append(
            AddonOption(
                code=code,
                name=name,
                price_cents=max(0, _safe_int(item.get("price_cents"), 0)),
            )
        )
    return result


def fallback_size_options(product_type: str | None, base_price_cents: int) -> list[SizeOption]:
    return parse_size_options(
        default_size_option_payloads(base_price_cents=base_price_cents, product_type=product_type),
        base_price_cents=base_price_cents,
    )


def resolve_size_options(
    raw: str | list[dict] | None,
    product_type: str | None,
    base_price_cents: int,
) -> list[SizeOption]:
    parsed = parse_size_options(raw, base_price_cents=base_price_cents)
    if parsed:
        return parsed
    return fallback_size_options(product_type=product_type, base_price_cents=base_price_cents)


def minimum_size_price_cents(options: list[SizeOption] | None, fallback: int = 0) -> int:
    items = list(options or [])
    if not items:
        return max(0, _safe_int(fallback))
    return min(item.price_cents for item in items)


def supports_sizes(options: list[SizeOption] | None) -> bool:
    return bool(options)


def supports_addons(options: list[AddonOption] | None) -> bool:
    return bool(options)


def normalized_size(code: str | None, options: list[SizeOption] | None) -> SizeOption | None:
    items = list(options or [])
    if not items:
        return None

    target_code = (code or "").strip()
    if target_code:
        for item in items:
            if item.code == target_code:
                return item
    return items[0]


def normalized_addons(codes: list[str] | None, options: list[AddonOption] | None) -> list[AddonOption]:
    items = list(options or [])
    if not items:
        return []

    addon_map = {item.code: item for item in items}
    result: list[AddonOption] = []
    seen_codes: set[str] = set()
    for raw_code in codes or []:
        code = (raw_code or "").strip()
        if not code or code in seen_codes:
            continue
        addon = addon_map.get(code)
        if addon is None:
            continue
        seen_codes.add(code)
        result.append(addon)
    return result


def build_line_name(product_name: str, size: SizeOption | None, addons: list[AddonOption]) -> str:
    parts = [product_name]
    if size is not None:
        parts.append(f"{size.name} {size.volume_label}")
    if addons:
        parts.append(", ".join(addon.name for addon in addons))
    return " / ".join(parts)
