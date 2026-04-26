const STORAGE_PREFIX = "coffee-flow-state-v4";
const PICKUP_PRESET_OFFSETS = [5, 10, 15];
const PHONE_SYNC_ATTEMPTS = 10;
const PHONE_SYNC_DELAY_MS = 1000;
const LOYALTY_GOAL_DEFAULT = 5;
const ORDERS_AUTO_REFRESH_MS = 15000;

const state = {
  me: null,
  banners: [],
  categories: [],
  products: [],
  productsById: new Map(),
  selectedCategorySlug: "all",
  searchQuery: "",
  pickupMode: "preset",
  selectedPickupOffset: PICKUP_PRESET_OFFSETS[0],
  customPickupText: "",
  consumptionPlace: "takeaway",
  cartItems: [],
  promoCode: "",
  bonusValue: "",
  note: "",
  orders: [],
  customize: {
    productId: null,
    sizeCode: null,
    addonCodes: [],
  },
  activeScreen: "home",
  storageReady: false,
  phoneRequestInFlight: false,
  autoPhonePromptDone: false,
  ordersRequestInFlight: false,
};

const nodes = {
  screens: Array.from(document.querySelectorAll(".screen")),
  navButtons: Array.from(document.querySelectorAll(".nav-item[data-screen]")),
  heroBonus: document.getElementById("heroBonus"),
  heroLoyaltyProgram: document.getElementById("heroLoyaltyProgram"),
  heroLoyaltyTrack: document.getElementById("heroLoyaltyTrack"),
  heroLoyaltyProgressText: document.getElementById("heroLoyaltyProgressText"),
  heroLoyaltyRewardCount: document.getElementById("heroLoyaltyRewardCount"),
  bannerList: document.getElementById("bannerList"),
  menuSection: document.getElementById("menuSection"),
  pickupSlotRow: document.getElementById("pickupSlotRow"),
  consumptionPlaceRow: document.getElementById("consumptionPlaceRow"),
  consumptionPlaceHint: document.getElementById("consumptionPlaceHint"),
  customTimeInput: document.getElementById("customTimeInput"),
  productSearchInput: document.getElementById("productSearchInput"),
  selectedPickupLabel: document.getElementById("selectedPickupLabel"),
  categoryChips: document.getElementById("categoryChips"),
  productGrid: document.getElementById("productGrid"),
  cartPickupTimeLabel: document.getElementById("cartPickupTimeLabel"),
  cartItems: document.getElementById("cartItems"),
  promoInput: document.getElementById("promoInput"),
  bonusField: document.getElementById("bonusField"),
  bonusInput: document.getElementById("bonusInput"),
  bonusMaxButton: document.getElementById("bonusMaxButton"),
  cartBonusBalance: document.getElementById("cartBonusBalance"),
  bonusBalanceHint: document.getElementById("bonusBalanceHint"),
  noteInput: document.getElementById("noteInput"),
  summarySubtotal: document.getElementById("summarySubtotal"),
  summaryBonusRow: document.getElementById("summaryBonusRow"),
  summaryBonus: document.getElementById("summaryBonus"),
  summaryLoyaltyRow: document.getElementById("summaryLoyaltyRow"),
  summaryLoyalty: document.getElementById("summaryLoyalty"),
  summaryFinal: document.getElementById("summaryFinal"),
  loyaltyPreviewHint: document.getElementById("loyaltyPreviewHint"),
  checkoutButton: document.getElementById("checkoutButton"),
  orderMessage: document.getElementById("orderMessage"),
  activeOrders: document.getElementById("activeOrders"),
  historyOrders: document.getElementById("historyOrders"),
  profileInitials: document.getElementById("profileInitials"),
  profileNameLabel: document.getElementById("profileNameLabel"),
  nameInput: document.getElementById("nameInput"),
  phoneStatus: document.getElementById("phoneStatus"),
  requestPhoneButton: document.getElementById("requestPhoneButton"),
  saveProfileButton: document.getElementById("saveProfileButton"),
  profileMessage: document.getElementById("profileMessage"),
  profileBonusRow: document.getElementById("profileBonusRow"),
  profileBonus: document.getElementById("profileBonus"),
  profileTelegram: document.getElementById("profileTelegram"),
  cartBadge: document.getElementById("cartBadge"),
  customizeModal: document.getElementById("customizeModal"),
  customizeTitle: document.getElementById("customizeTitle"),
  closeCustomizeButton: document.getElementById("closeCustomizeButton"),
  customizePrice: document.getElementById("customizePrice"),
  sizeOptionsWrap: document.getElementById("sizeOptionsWrap"),
  sizeOptions: document.getElementById("sizeOptions"),
  addonOptionsWrap: document.getElementById("addonOptionsWrap"),
  addonOptions: document.getElementById("addonOptions"),
  addConfiguredProductButton: document.getElementById("addConfiguredProductButton"),
};

let lockedScrollTop = 0;
let bannerRotationTimer = null;
let bannerRotationIndex = 0;

function getTelegramWebApp() {
  return window.Telegram?.WebApp ?? null;
}

function getTelegramInitData() {
  return getTelegramWebApp()?.initData?.trim() || "";
}

function notifyUser(message) {
  const tg = getTelegramWebApp();
  if (tg?.showAlert) {
    tg.showAlert(message);
    return;
  }
  window.alert(message);
}

function showMessage(node, text, kind = "success") {
  if (!node) {
    return;
  }
  node.textContent = text;
  node.classList.remove("hidden", "error");
  if (kind === "error") {
    node.classList.add("error");
  }
}

function clearMessage(node) {
  if (!node) {
    return;
  }
  node.textContent = "";
  node.classList.add("hidden");
  node.classList.remove("error");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatMoney(cents) {
  return `${(Number(cents || 0) / 100).toFixed(2)} BYN`;
}

function formatMoneyInput(cents) {
  return (Number(cents || 0) / 100).toFixed(2);
}

function formatDateTime(value) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return new Intl.DateTimeFormat("ru-BY", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function parseMoneyToCents(value) {
  const normalized = String(value ?? "").trim().replace(",", ".");
  if (!normalized) {
    return 0;
  }
  const parsed = Number(normalized);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return 0;
  }
  return Math.round(parsed * 100);
}

function parsePositiveInt(value, fallback = 1) {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return fallback;
  }
  return parsed;
}

function normalizeApiValidationMessage(message) {
  const normalized = String(message ?? "").trim();
  if (!normalized) {
    return "содержит некорректное значение";
  }
  const rules = [
    [/^Field required$/i, "обязательно для заполнения"],
    [/^String should have at least (\d+) characters?$/i, "должно содержать минимум $1 символов"],
    [/^String should have at most (\d+) characters?$/i, "не должно быть длиннее $1 символов"],
    [/^Input should be greater than or equal to (-?\d+(?:\.\d+)?)$/i, "не должно быть меньше $1"],
    [/^Input should be less than or equal to (-?\d+(?:\.\d+)?)$/i, "не должно быть больше $1"],
    [/^Input should be a valid integer.*$/i, "должно быть целым числом"],
    [/^Input should be a valid number.*$/i, "должно быть числом"],
    [/^Input should be a valid string$/i, "должно быть строкой"],
    [/^Input should be a valid boolean.*$/i, "должно быть переключателем да/нет"],
    [/^Value error, (.+)$/i, "$1"],
  ];
  for (const [pattern, replacement] of rules) {
    if (pattern.test(normalized)) {
      return normalized.replace(pattern, replacement);
    }
  }
  return normalized;
}

function getApiErrorMessage(detail, fallback = "Не удалось выполнить запрос.") {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail) && detail.length) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== "object") {
          return null;
        }
        const path = Array.isArray(item.loc)
          ? item.loc.filter((part) => !["body", "query", "path"].includes(String(part)))
          : [];
        const fieldName = path.length ? `Поле "${path[path.length - 1]}"` : "Запрос";
        return `${fieldName}: ${normalizeApiValidationMessage(item.msg)}.`;
      })
      .filter(Boolean);
    return messages.join(" ") || fallback;
  }
  if (detail && typeof detail === "object") {
    if (typeof detail.message === "string" && detail.message.trim()) {
      return detail.message.trim();
    }
    try {
      return JSON.stringify(detail);
    } catch {
      return fallback;
    }
  }
  return fallback;
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function getStorageKey() {
  const suffix = state.me?.telegram_id ? String(state.me.telegram_id) : "guest";
  return `${STORAGE_PREFIX}:${suffix}`;
}

function getStoredState() {
  const keys = [getStorageKey(), `${STORAGE_PREFIX}:guest`, STORAGE_PREFIX];
  for (const key of keys) {
    try {
      const raw = window.localStorage.getItem(key);
      if (!raw) {
        continue;
      }
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        return parsed;
      }
    } catch {
      return null;
    }
  }
  return null;
}

function persistState() {
  if (!state.storageReady) {
    return;
  }
  const payload = {
    category_slug: state.selectedCategorySlug,
    search_query: state.searchQuery,
      pickup_mode: state.pickupMode,
      pickup_offset: state.selectedPickupOffset,
      custom_pickup_text: state.customPickupText,
      consumption_place: state.consumptionPlace,
      promo_code: state.promoCode,
    bonus_value: state.bonusValue,
    note: state.note,
    items: state.cartItems.map((item) => ({
      product_id: item.product_id,
      qty: item.qty,
      size_code: item.size_code,
      addon_codes: item.addon_codes,
    })),
  };
  try {
    window.localStorage.setItem(getStorageKey(), JSON.stringify(payload));
  } catch {
    // Ignore storage errors in restricted webviews.
  }
}

function getProductById(productId) {
  return state.productsById.get(Number(productId)) || null;
}

function getProductSizeOptions(product) {
  return Array.isArray(product?.size_options) ? product.size_options : [];
}

function getProductAddonOptions(product) {
  return Array.isArray(product?.addon_options) ? product.addon_options : [];
}

function getProductMinPrice(product) {
  const sizeOptions = getProductSizeOptions(product);
  if (!sizeOptions.length) {
    return Number(product?.price_cents || 0);
  }
  return sizeOptions.reduce((minPrice, option) => {
    const optionPrice = Number(option.price_cents || 0);
    return optionPrice < minPrice ? optionPrice : minPrice;
  }, Number(sizeOptions[0].price_cents || 0));
}

function getNormalizedSizeOption(product, sizeCode) {
  const options = getProductSizeOptions(product);
  if (!options.length) {
    return null;
  }
  return options.find((item) => item.code === sizeCode) || options[0];
}

function getNormalizedAddonOptions(product, addonCodes) {
  const options = getProductAddonOptions(product);
  if (!options.length) {
    return [];
  }
  const selected = new Set(Array.isArray(addonCodes) ? addonCodes : []);
  return options.filter((item) => selected.has(item.code));
}

function getCartItemKey(item) {
  const addonCodes = [...(item.addon_codes || [])].sort();
  return [item.product_id, item.size_code || "", addonCodes.join(",")].join("|");
}

function buildCartLineLabel(product, item) {
  const parts = [];
  const size = getNormalizedSizeOption(product, item.size_code);
  const addons = getNormalizedAddonOptions(product, item.addon_codes);
  if (size) {
    parts.push(`${size.name} ${size.volume_label}`);
  }
  if (addons.length) {
    parts.push(addons.map((addon) => addon.name).join(", "));
  }
  return parts.join(" / ");
}

function getUnitPrice(product, item) {
  const size = getNormalizedSizeOption(product, item.size_code);
  const addons = getNormalizedAddonOptions(product, item.addon_codes);
  const basePrice = size ? Number(size.price_cents || 0) : Number(product.price_cents || 0);
  const addonsTotal = addons.reduce((sum, addon) => sum + Number(addon.price_cents || 0), 0);
  return basePrice + addonsTotal;
}

function getCartSubtotal() {
  return state.cartItems.reduce((sum, item) => {
    const product = getProductById(item.product_id);
    if (!product) {
      return sum;
    }
    return sum + getUnitPrice(product, item) * item.qty;
  }, 0);
}

function getLoyaltyState() {
  const goal = Math.max(1, Number(state.me?.loyalty_goal || LOYALTY_GOAL_DEFAULT));
  const progress = Math.max(0, Math.min(Number(state.me?.loyalty_progress || 0), goal));
  const rewardsAvailable = Math.max(0, Number(state.me?.loyalty_rewards_available || 0));
  return { goal, progress, rewardsAvailable };
}

function getLoyaltyCategorySlugs() {
  const rawValue = Array.isArray(state.me?.loyalty_category_slugs) && state.me?.loyalty_category_slugs.length
    ? state.me.loyalty_category_slugs
    : [state.me?.loyalty_category_slug || "coffee"];
  return rawValue
    .map((value) => String(value ?? "").trim().toLowerCase())
    .filter(Boolean);
}

function getLoyaltyCategorySlug() {
  return getLoyaltyCategorySlugs()[0] || "coffee";
}

function getLoyaltyCategoryLabels() {
  return getLoyaltyCategorySlugs().map((slug) => {
    const category = state.categories.find((item) => item.slug === slug);
    return category?.name || slug;
  });
}

function getLoyaltyCategoryLabelText() {
  const labels = getLoyaltyCategoryLabels();
  if (!labels.length) {
    return 'категории "кофе"';
  }
  if (labels.length === 1) {
    return `категории "${labels[0]}"`;
  }
  return `категорий "${labels.join('", "')}"`;
}

function isBonusProgramVisible() {
  return Boolean(state.me?.bonus_enabled || state.me?.bonus_redeem_enabled);
}

function canSpendBonuses() {
  return Boolean(state.me?.bonus_redeem_enabled);
}

function isLoyaltyProduct(product) {
  const targetSlugs = getLoyaltyCategorySlugs();
  return targetSlugs.includes(String(product?.category_slug || "").trim().toLowerCase())
    || targetSlugs.includes(String(product?.product_type || "").trim().toLowerCase());
}

function getLoyaltyPreview() {
  const { goal, progress: initialProgress, rewardsAvailable: initialRewards } = getLoyaltyState();
  const qualifyingUnitPrices = [];

  for (const item of state.cartItems) {
    const product = getProductById(item.product_id);
    if (!product || !isLoyaltyProduct(product)) {
      continue;
    }

    const unitPrice = getUnitPrice(product, item);
    for (let index = 0; index < item.qty; index += 1) {
      qualifyingUnitPrices.push(unitPrice);
    }
  }

  const totalUnits = qualifyingUnitPrices.length;
  let paidUnits = totalUnits;
  for (let candidatePaidUnits = 0; candidatePaidUnits <= totalUnits; candidatePaidUnits += 1) {
    const earnedRewards = Math.floor((initialProgress + candidatePaidUnits) / goal);
    const availableRewards = initialRewards + earnedRewards;
    const candidateFreeUnits = totalUnits - candidatePaidUnits;
    if (candidateFreeUnits <= availableRewards) {
      paidUnits = candidatePaidUnits;
      break;
    }
  }
  const freeCoffeeCount = Math.max(0, totalUnits - paidUnits);
  const sortedPrices = [...qualifyingUnitPrices].sort((left, right) => left - right);
  const discountCents = sortedPrices.slice(0, freeCoffeeCount).reduce((sum, price) => sum + price, 0);
  const earnedRewards = Math.floor((initialProgress + paidUnits) / goal);
  const progress = (initialProgress + paidUnits) % goal;
  const rewardsAvailable = Math.max(0, initialRewards + earnedRewards - freeCoffeeCount);

  return { discountCents, freeCoffeeCount, progress, rewardsAvailable };
}

function getMaxBonusSpendCents() {
  if (!canSpendBonuses()) {
    return 0;
  }
  const subtotal = getCartSubtotal();
  const loyaltyDiscount = getLoyaltyPreview().discountCents;
  const remainingAfterDiscounts = Math.max(0, subtotal - loyaltyDiscount);
  const available = Number(state.me?.bonus_balance || 0);
  const percentLimit = remainingAfterDiscounts * Number(state.me?.bonus_redeem_max_percent ?? 100) / 100;
  return Math.min(available, remainingAfterDiscounts, Math.floor(percentLimit));
}

function getBonusSpendState() {
  const requested = parseMoneyToCents(state.bonusValue);
  const maxAvailable = getMaxBonusSpendCents();
  const bonusBalance = Number(state.me?.bonus_balance || 0);
  if (!canSpendBonuses()) {
    return { requested, applied: 0, maxAvailable: 0, isValid: requested <= 0, error: "" };
  }
  if (!requested) {
    return { requested: 0, applied: 0, maxAvailable, isValid: true, error: "" };
  }
  if (requested > bonusBalance) {
    return {
      requested,
      applied: 0,
      maxAvailable,
      isValid: false,
      error: `Нельзя списать больше бонусов, чем у вас есть. Сейчас на счёте: ${formatMoney(bonusBalance)}.`,
    };
  }
  if (requested > maxAvailable) {
    const percentLabel = Number(state.me?.bonus_redeem_max_percent ?? 100);
    return {
      requested,
      applied: 0,
      maxAvailable,
      isValid: false,
      error: `Нельзя использовать бонусов больше, чем ${percentLabel}% от заказа. Сейчас максимум: ${formatMoney(maxAvailable)}.`,
    };
  }
  return { requested, applied: requested, maxAvailable, isValid: true, error: "" };
}

function getLoyaltyValueText() {
  const { goal, progress, rewardsAvailable } = getLoyaltyState();
  if (rewardsAvailable > 0) {
    return `${rewardsAvailable} бесплатно`;
  }
  return `${progress}/${goal}`;
}

function getLoyaltyHintText() {
  const categoryLabel = getLoyaltyCategoryLabelText();
  const { goal, progress, rewardsAvailable } = getLoyaltyState();
  if (rewardsAvailable > 0) {
    return `Доступно бесплатно: ${rewardsAvailable} из ${categoryLabel}.`;
  }
  return `До бесплатного напитка из ${categoryLabel}: ${Math.max(1, goal - progress)}.`;
}

function getLoyaltyProgramText() {
  const categoryLabel = getLoyaltyCategoryLabelText();
  const { goal } = getLoyaltyState();
  return `Каждый ${goal + 1}-й напиток из ${categoryLabel} бесплатно`;
}

function pluralizeDrink(count) {
  const normalized = Math.abs(Number(count || 0)) % 100;
  const lastDigit = normalized % 10;
  if (normalized > 10 && normalized < 20) {
    return "напитков";
  }
  if (lastDigit === 1) {
    return "напиток";
  }
  if (lastDigit >= 2 && lastDigit <= 4) {
    return "напитка";
  }
  return "напитков";
}

function getLoyaltyPreviewHint(loyaltyPreview) {
  const { goal } = getLoyaltyState();
  if (!loyaltyPreview?.freeCoffeeCount) {
    return "";
  }
  const displayProgress = loyaltyPreview.rewardsAvailable > 0 && loyaltyPreview.progress === 0
    ? goal
    : loyaltyPreview.progress;
  return `По лояльности бесплатно: ${loyaltyPreview.freeCoffeeCount} ${pluralizeDrink(loyaltyPreview.freeCoffeeCount)}. После заказа в новом цикле будет ${displayProgress} из ${goal}.`;
}

function buildLoyaltyTrackMarkup() {
  const { goal, progress, rewardsAvailable } = getLoyaltyState();
  const steps = [];
  for (let index = 0; index < goal; index += 1) {
    steps.push(`
      <span class="loyalty-step ${index < progress ? "active" : ""}">
        <span>${index + 1}</span>
      </span>
    `);
  }
  steps.push(`
    <span class="loyalty-step reward ${rewardsAvailable > 0 ? "active" : ""}">
      <span>☕</span>
    </span>
  `);
  return steps.join("");
}
function getCartCount() {
  return state.cartItems.reduce((sum, item) => sum + Number(item.qty || 0), 0);
}

function getPresetDeliveryTime(offsetMinutes) {
  const now = new Date();
  const target = new Date(now.getTime() + offsetMinutes * 60 * 1000);
  const hours = String(target.getHours()).padStart(2, "0");
  const minutes = String(target.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

function getPickupRequestValue() {
  if (state.pickupMode === "custom" && state.customPickupText.trim()) {
    return state.customPickupText.trim();
  }
  return `+${state.selectedPickupOffset}`;
}

function getPickupDisplayLabel() {
  if (state.pickupMode === "custom" && state.customPickupText.trim()) {
    return state.customPickupText.trim();
  }
  return `Через ${state.selectedPickupOffset} минут`;
}

function getConsumptionPlaceLabel(value) {
  return value === "dine_in" ? "На месте" : "С собой";
}

function applyBootstrap(data) {
  state.me = data.me || null;
  state.banners = Array.isArray(data.banners) ? data.banners : [];
  state.categories = Array.isArray(data.categories) ? data.categories : [];
  state.products = Array.isArray(data.products) ? data.products : [];
  state.productsById = new Map(state.products.map((product) => [Number(product.id), product]));

  const hasSelectedCategory = state.selectedCategorySlug === "all"
    || state.categories.some((item) => item.slug === state.selectedCategorySlug);
  if (!hasSelectedCategory) {
    state.selectedCategorySlug = "all";
  }
}

function sanitizeCartItems(items) {
  if (!Array.isArray(items)) {
    return [];
  }
  const sanitized = [];
  for (const rawItem of items) {
    const product = getProductById(rawItem?.product_id);
    if (!product) {
      continue;
    }
    const size = getNormalizedSizeOption(product, rawItem.size_code || null);
    const addons = getNormalizedAddonOptions(product, rawItem.addon_codes);
    sanitized.push({
      product_id: product.id,
      qty: Math.min(parsePositiveInt(rawItem.qty, 1), 50),
      size_code: size?.code || null,
      addon_codes: addons.map((addon) => addon.code),
    });
  }
  return sanitized;
}

function restoreStateFromStorage() {
  const stored = getStoredState();
  if (stored) {
    state.selectedCategorySlug = typeof stored.category_slug === "string" ? stored.category_slug : "all";
    state.searchQuery = typeof stored.search_query === "string" ? stored.search_query : "";
    state.pickupMode = stored.pickup_mode === "custom" ? "custom" : "preset";
    state.selectedPickupOffset = PICKUP_PRESET_OFFSETS.includes(Number(stored.pickup_offset))
      ? Number(stored.pickup_offset)
      : PICKUP_PRESET_OFFSETS[0];
    state.customPickupText = typeof stored.custom_pickup_text === "string" ? stored.custom_pickup_text : "";
    state.consumptionPlace = stored.consumption_place === "dine_in" ? "dine_in" : "takeaway";
    state.promoCode = typeof stored.promo_code === "string" ? stored.promo_code : "";
    state.bonusValue = typeof stored.bonus_value === "string" ? stored.bonus_value : "";
    state.note = typeof stored.note === "string" ? stored.note : "";
    state.cartItems = sanitizeCartItems(stored.items);
  }

  const validCategory = state.selectedCategorySlug === "all"
    || state.categories.some((item) => item.slug === state.selectedCategorySlug);
  if (!validCategory) {
    state.selectedCategorySlug = "all";
  }
  if (state.pickupMode !== "custom") {
    state.pickupMode = "preset";
  }
  syncFormInputs();
  state.storageReady = true;
  persistState();
}

function syncFormInputs() {
  nodes.customTimeInput.value = state.pickupMode === "custom" ? state.customPickupText : "";
  nodes.productSearchInput.value = state.searchQuery;
  nodes.promoInput.value = state.promoCode;
  nodes.bonusInput.value = state.bonusValue;
  nodes.noteInput.value = state.note;
  nodes.nameInput.value = state.me?.full_name || "";
}

function getInitials(value) {
  const parts = String(value || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);
  if (!parts.length) {
    return "CF";
  }
  return parts.map((part) => part[0]?.toUpperCase() || "").join("") || "CF";
}

function renderTopLevel() {
  const heroHint = document.getElementById("heroLoyaltyHint");
  const bonusBalanceText = formatMoney(state.me?.bonus_balance || 0);
  const { goal, progress, rewardsAvailable } = getLoyaltyState();
  const showBonusProgram = isBonusProgramVisible();

  nodes.heroBonus.textContent = getLoyaltyValueText();
  nodes.profileBonus.textContent = bonusBalanceText;
  nodes.profileBonusRow?.classList.toggle("hidden", !showBonusProgram);
  if (nodes.heroLoyaltyProgram) {
    nodes.heroLoyaltyProgram.textContent = getLoyaltyProgramText();
  }
  if (nodes.heroLoyaltyTrack) {
    nodes.heroLoyaltyTrack.innerHTML = buildLoyaltyTrackMarkup();
  }
  if (nodes.heroLoyaltyProgressText) {
    nodes.heroLoyaltyProgressText.textContent = `${progress} из ${goal}`;
  }
  if (nodes.heroLoyaltyRewardCount) {
    nodes.heroLoyaltyRewardCount.textContent = String(rewardsAvailable);
  }
  if (heroHint) {
    heroHint.textContent = getLoyaltyHintText();
  }
  nodes.profileNameLabel.textContent = state.me?.full_name || "Ваш профиль";
  nodes.profileTelegram.textContent = state.me?.username ? `@${state.me.username}` : "Telegram";
  nodes.profileInitials.textContent = getInitials(state.me?.full_name || state.me?.username || "Coffee Flow");
  nodes.phoneStatus.textContent = state.me?.phone || "Телефон еще не подтвержден";
  nodes.requestPhoneButton.textContent = state.me?.phone
    ? "Обновить телефон из Telegram"
    : "Получить телефон из Telegram";
}
function renderBanners() {
  if (!state.banners.length) {
    nodes.bannerList.innerHTML = '<article class="empty-card"><h3>Акций пока нет</h3><p>Но меню уже можно собрать и оформить.</p></article>';
    if (bannerRotationTimer) {
      window.clearInterval(bannerRotationTimer);
      bannerRotationTimer = null;
    }
    return;
  }

  bannerRotationIndex = Math.min(bannerRotationIndex, Math.max(0, state.banners.length - 1));
  nodes.bannerList.innerHTML = state.banners
    .map((banner) => `
      <article class="banner-card">
        <img src="${escapeHtml(banner.image_url || "/static/images/banner-week.svg")}" alt="${escapeHtml(banner.title)}" />
        <div class="banner-content">
          ${banner.subtitle ? `<span class="banner-subtitle">${escapeHtml(banner.subtitle)}</span>` : ""}
          <h4>${escapeHtml(banner.title)}</h4>
          ${banner.description ? `<p>${escapeHtml(banner.description)}</p>` : ""}
        </div>
      </article>
    `)
    .join("");

  if (bannerRotationTimer) {
    window.clearInterval(bannerRotationTimer);
  }
  if (state.banners.length > 1) {
    bannerRotationTimer = window.setInterval(() => {
      if (document.hidden || state.activeScreen !== "home") {
        return;
      }
      const cards = nodes.bannerList.querySelectorAll(".banner-card");
      if (!cards.length) {
        return;
      }
      bannerRotationIndex = (bannerRotationIndex + 1) % cards.length;
      const targetCard = cards[bannerRotationIndex];
      const scrollLeft = targetCard?.offsetLeft || 0;
      nodes.bannerList.scrollTo({ left: scrollLeft, behavior: "smooth" });
    }, 4500);
  } else {
    bannerRotationTimer = null;
  }
}

function renderPickupControls() {
  nodes.pickupSlotRow.innerHTML = PICKUP_PRESET_OFFSETS
    .map((offset) => `
      <button class="chip ${state.pickupMode === "preset" && offset === state.selectedPickupOffset ? "active" : ""}" type="button" data-pickup-offset="${offset}">
        +${offset} мин • ${escapeHtml(getPresetDeliveryTime(offset))}
      </button>
    `)
    .join("");
  if (nodes.selectedPickupLabel) {
    nodes.selectedPickupLabel.textContent = getPickupDisplayLabel();
  }
  nodes.cartPickupTimeLabel.textContent = getPickupDisplayLabel();
  nodes.customTimeInput.value = state.pickupMode === "custom" ? state.customPickupText : "";
  if (nodes.consumptionPlaceRow) {
    const buttons = Array.from(nodes.consumptionPlaceRow.querySelectorAll("[data-consumption-place]"));
    buttons.forEach((button) => {
      button.classList.toggle("active", button.dataset.consumptionPlace === state.consumptionPlace);
    });
  }
  if (nodes.consumptionPlaceHint) {
    nodes.consumptionPlaceHint.textContent = `Бариста увидит отметку: ${getConsumptionPlaceLabel(state.consumptionPlace)}.`;
  }
}

function renderCategories() {
  const chips = [
    `<button class="chip ${state.selectedCategorySlug === "all" ? "active" : ""}" type="button" data-category-select="all">Все</button>`,
  ];
  for (const category of state.categories) {
    chips.push(`
      <button class="chip ${category.slug === state.selectedCategorySlug ? "active" : ""}" type="button" data-category-select="${escapeHtml(category.slug)}">
        ${escapeHtml(category.name)}
      </button>
    `);
  }
  nodes.categoryChips.innerHTML = chips.join("");
}

function getFilteredProducts() {
  const normalizedQuery = state.searchQuery.trim().toLowerCase();
  return state.products.filter((product) => {
    const matchesCategory = state.selectedCategorySlug === "all" || product.category_slug === state.selectedCategorySlug;
    if (!matchesCategory) {
      return false;
    }
    if (!normalizedQuery) {
      return true;
    }
    return String(product.name || "").toLowerCase().includes(normalizedQuery);
  });
}

function getProductMeta(product) {
  const parts = [];
  if (product.composition) {
    parts.push(product.composition);
  }
  const specs = [
    product.calories_kcal ? `${product.calories_kcal} ккал` : null,
  ].filter(Boolean);
  if (specs.length) {
    parts.push(specs.join(' / '));
  }
  return parts;
}
function getProductOptionSummary(product) {
  const summary = [];
  const sizeOptions = getProductSizeOptions(product);
  const addonOptions = getProductAddonOptions(product);
  if (sizeOptions.length) {
    summary.push(sizeOptions.length === 1 ? "1 размер" : `${sizeOptions.length} размеров`);
  }
  if (addonOptions.length) {
    summary.push(addonOptions.length === 1 ? "1 доп" : `${addonOptions.length} допов`);
  }
  return summary.join(" • ") || "Готов к покупке";
}

function renderProducts() {
  const products = getFilteredProducts();
  if (!products.length) {
    nodes.productGrid.innerHTML = '<article class="empty-card"><h3>Ничего не найдено</h3><p>Попробуйте другую категорию или измените поисковый запрос.</p></article>';
    return;
  }

  nodes.productGrid.innerHTML = products
    .map((product) => {
      const meta = getProductMeta(product);
      const minPrice = getProductMinPrice(product);
      const sizeOptions = getProductSizeOptions(product);
      const priceLabel = sizeOptions.length > 1 ? `от ${formatMoney(minPrice)}` : formatMoney(minPrice);
      return `
        <article class="product-card" data-product-action="${product.id}" tabindex="0" role="button" aria-label="Выбрать ${escapeHtml(product.name)}">
          <img src="${escapeHtml(product.image_url || "/static/images/latte.svg")}" alt="${escapeHtml(product.name)}" />
          <div class="product-info">
            <div class="product-top">
              <div>
                ${product.badge ? `<span class="badge">${escapeHtml(product.badge)}</span>` : ""}
                <h4>${escapeHtml(product.name)}</h4>
              </div>
              <strong>${escapeHtml(priceLabel)}</strong>
            </div>
            ${product.description ? `<p>${escapeHtml(product.description)}</p>` : ""}
            ${meta.length ? `<div class="branch-meta">${meta.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>` : ""}
            <div class="product-actions">
              <span class="count-caption">${escapeHtml(getProductOptionSummary(product))}</span>
              <span class="secondary-button product-cta">Купить</span>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderCartBadge() {
  const count = getCartCount();
  nodes.cartBadge.textContent = String(count);
  nodes.cartBadge.classList.toggle("hidden", count <= 0);
}

function renderCart() {
  if (!state.cartItems.length) {
    nodes.cartItems.innerHTML = '<article class="empty-cart"><h3>Корзина пока пустая</h3><p>Выберите товар в меню и добавьте его в заказ.</p></article>';
  } else {
    nodes.cartItems.innerHTML = state.cartItems
      .map((item) => {
        const product = getProductById(item.product_id);
        if (!product) {
          return "";
        }
        const itemKey = getCartItemKey(item);
        const lineLabel = buildCartLineLabel(product, item);
        const unitPrice = getUnitPrice(product, item);
        const total = unitPrice * item.qty;
        return `
          <article class="cart-item">
            <img src="${escapeHtml(product.image_url || "/static/images/latte.svg")}" alt="${escapeHtml(product.name)}" />
            <div class="cart-item-content">
              <div class="cart-item-top">
                <div>
                  <strong>${escapeHtml(product.name)}</strong>
                  ${lineLabel ? `<p>${escapeHtml(lineLabel)}</p>` : ""}
                </div>
                <strong>${formatMoney(total)}</strong>
              </div>
              <div class="branch-meta">
                <span>${formatMoney(unitPrice)} за шт.</span>
                <span>${item.qty} шт.</span>
              </div>
              <div class="cart-item-actions">
                <div class="quantity-controls">
                  <button class="secondary-button" type="button" data-cart-action="decrease" data-cart-key="${escapeHtml(itemKey)}">-</button>
                  <span class="count-caption">${item.qty} шт.</span>
                  <button class="secondary-button" type="button" data-cart-action="increase" data-cart-key="${escapeHtml(itemKey)}">+</button>
                </div>
                <button class="link-button" type="button" data-cart-action="remove" data-cart-key="${escapeHtml(itemKey)}">Удалить</button>
              </div>
            </div>
          </article>
        `;
      })
      .join("");
  }

  const subtotal = getCartSubtotal();
  const loyaltyPreview = getLoyaltyPreview();
  const bonusState = getBonusSpendState();
  const bonusBalance = Number(state.me?.bonus_balance || 0);
  const maxBonusSpend = bonusState.maxAvailable;
  const showBonusField = canSpendBonuses();
  if (!showBonusField && state.bonusValue) {
    state.bonusValue = "";
    persistState();
  }
  nodes.bonusField?.classList.toggle("hidden", !showBonusField);
  nodes.summaryBonusRow?.classList.toggle("hidden", !showBonusField);
  nodes.summaryLoyaltyRow?.classList.toggle("hidden", loyaltyPreview.discountCents <= 0);
  nodes.summarySubtotal.textContent = formatMoney(subtotal);
  nodes.summaryBonus.textContent = bonusState.applied ? `-${formatMoney(bonusState.applied)}` : formatMoney(0);
  if (nodes.summaryLoyalty) {
    nodes.summaryLoyalty.textContent = loyaltyPreview.discountCents ? `-${formatMoney(loyaltyPreview.discountCents)}` : formatMoney(0);
  }
  nodes.summaryFinal.textContent = formatMoney(Math.max(0, subtotal - loyaltyPreview.discountCents - bonusState.applied));
  nodes.bonusInput.value = showBonusField ? state.bonusValue : "";
  nodes.bonusInput.max = formatMoneyInput(maxBonusSpend);
  nodes.bonusInput.disabled = !showBonusField;
  if (nodes.cartBonusBalance) {
    nodes.cartBonusBalance.textContent = formatMoney(bonusBalance);
  }
  if (nodes.bonusBalanceHint) {
    const percentLabel = Number(state.me?.bonus_redeem_max_percent ?? 100);
    nodes.bonusBalanceHint.classList.toggle("error", Boolean(showBonusField && bonusState.error));
    if (showBonusField && bonusState.error) {
      nodes.bonusBalanceHint.textContent = bonusState.error;
    } else if (bonusBalance <= 0) {
      nodes.bonusBalanceHint.textContent = "Бонусов пока нет. После завершения заказов они появятся здесь.";
    } else if (maxBonusSpend <= 0) {
      nodes.bonusBalanceHint.textContent = `Списать бонусы в этом заказе сейчас нельзя. Максимум: ${formatMoney(0)}.`;
    } else {
      nodes.bonusBalanceHint.textContent = `Максимально можно списать ${formatMoney(maxBonusSpend)}. Это до ${percentLabel}% от текущего заказа.`;
    }
  }
  if (nodes.bonusMaxButton) {
    nodes.bonusMaxButton.classList.toggle("hidden", !showBonusField);
    nodes.bonusMaxButton.disabled = maxBonusSpend <= 0;
  }
  if (nodes.loyaltyPreviewHint) {
    const loyaltyHint = getLoyaltyPreviewHint(loyaltyPreview);
    nodes.loyaltyPreviewHint.textContent = loyaltyHint;
    nodes.loyaltyPreviewHint.classList.toggle("hidden", !loyaltyHint);
  }
  nodes.checkoutButton.disabled = !state.cartItems.length || (showBonusField && !bonusState.isValid);
  renderCartBadge();
}

function getStatusLabel(status) {
  const labels = {
    new: "Новый",
    in_progress: "Готовим",
    ready: "Готов",
    en_route: "В пути",
    completed: "Завершен",
    cancelled: "Отменен",
  };
  return labels[status] || status;
}

function getOrderPickupLabel(order) {
  return order.pickup_label || formatDateTime(order.scheduled_for) || "Как можно скорее";
}

function canCancelOrder(status) {
  return status === "new" || status === "in_progress";
}

function buildOrderCard(order, history = false) {
  const itemsMarkup = Array.isArray(order.items) && order.items.length
    ? `
      <ul class="order-items-list">
        ${order.items.map((item) => `
          <li class="order-item-row">
            <span>${escapeHtml(item.name_snapshot)}</span>
            <strong>x${escapeHtml(item.qty)}</strong>
          </li>
        `).join("")}
      </ul>
    `
    : "";
  const wrapperClass = history ? "history-card" : "order-card";

  return `
    <article class="${wrapperClass}">
      <div class="order-card-head">
        <div>
          <strong>Заказ №${escapeHtml(order.order_number)}</strong>
          <p class="order-main-text">Самовывоз: ${escapeHtml(getOrderPickupLabel(order))}</p>
          <p class="history-text">Подача: ${escapeHtml(getConsumptionPlaceLabel(order.consumption_place))}</p>
        </div>
        <span class="status-chip status-${escapeHtml(order.status)}">${escapeHtml(getStatusLabel(order.status))}</span>
      </div>
      ${itemsMarkup}
      <div class="branch-meta">
        ${order.created_at ? `<span>Создан: ${escapeHtml(formatDateTime(order.created_at))}</span>` : ""}
        <span>Итого: ${escapeHtml(formatMoney(order.final_cents))}</span>
      </div>
      ${!history && canCancelOrder(order.status) ? `
        <div class="order-card-foot">
          <button class="secondary-button" type="button" data-order-cancel="${escapeHtml(order.id)}">Отменить заказ</button>
        </div>
      ` : ""}
    </article>
  `;
}

function renderOrders() {
  const activeOrders = state.orders.filter((order) => !["completed", "cancelled"].includes(order.status));
  const historyOrders = state.orders.filter((order) => ["completed", "cancelled"].includes(order.status));

  nodes.activeOrders.innerHTML = activeOrders.length
    ? activeOrders.map((order) => buildOrderCard(order)).join("")
    : '<article class="empty-card"><h3>Активных заказов нет</h3><p>Когда оформите новый заказ, его статус появится здесь.</p></article>';

  nodes.historyOrders.innerHTML = historyOrders.length
    ? historyOrders.map((order) => buildOrderCard(order, true)).join("")
    : '<article class="empty-card"><h3>История пока пустая</h3><p>Здесь будут завершенные и отмененные заказы.</p></article>';
}

let ordersRefreshTimer = null;

function hasLiveOrders(orders = state.orders) {
  return orders.some((order) => !["completed", "cancelled"].includes(order.status));
}

function getOrdersSignature(orders = state.orders) {
  return orders
    .map((order) => `${order.id}:${order.status}`)
    .sort()
    .join("|");
}

function stopOrdersAutoRefresh() {
  if (ordersRefreshTimer) {
    window.clearInterval(ordersRefreshTimer);
    ordersRefreshTimer = null;
  }
}

function startOrdersAutoRefresh() {
  if (ordersRefreshTimer) {
    return;
  }
  ordersRefreshTimer = window.setInterval(() => {
    if (document.hidden) {
      return;
    }
    if (state.activeScreen !== "orders" && !hasLiveOrders()) {
      stopOrdersAutoRefresh();
      return;
    }
    loadOrders({ silent: true });
  }, ORDERS_AUTO_REFRESH_MS);
}

function syncOrdersAutoRefresh() {
  if (document.hidden) {
    stopOrdersAutoRefresh();
    return;
  }
  if (state.activeScreen === "orders" || hasLiveOrders()) {
    startOrdersAutoRefresh();
    return;
  }
  stopOrdersAutoRefresh();
}

function renderCustomizeModal() {
  const product = getProductById(state.customize.productId);
  if (!product) {
    return;
  }

  const sizeOptions = getProductSizeOptions(product);
  const addonOptions = getProductAddonOptions(product);
  const selectedItem = {
    product_id: product.id,
    qty: 1,
    size_code: state.customize.sizeCode,
    addon_codes: state.customize.addonCodes,
  };

  nodes.customizeTitle.textContent = product.name;
  nodes.customizePrice.textContent = formatMoney(getUnitPrice(product, selectedItem));

  nodes.sizeOptionsWrap.classList.toggle("hidden", sizeOptions.length <= 1);
  nodes.addonOptionsWrap.classList.toggle("hidden", !addonOptions.length);

  nodes.sizeOptions.innerHTML = sizeOptions
    .map((option) => `
      <button class="option-card ${option.code === state.customize.sizeCode ? "active" : ""}" type="button" data-size-option="${escapeHtml(option.code)}">
        <strong>${escapeHtml(option.name)}</strong>
        <span>${escapeHtml(option.volume_label)}</span>
        <small>${formatMoney(option.price_cents)}</small>
      </button>
    `)
    .join("");

  nodes.addonOptions.innerHTML = addonOptions
    .map((option) => `
      <button class="option-card ${state.customize.addonCodes.includes(option.code) ? "active" : ""}" type="button" data-addon-option="${escapeHtml(option.code)}">
        <strong>${escapeHtml(option.name)}</strong>
        <small>${formatMoney(option.price_cents)}</small>
      </button>
    `)
    .join("");
}

function renderAll() {
  renderTopLevel();
  renderBanners();
  renderPickupControls();
  renderCategories();
  renderProducts();
  renderCart();
  renderOrders();
}

function switchScreen(screenName) {
  if (nodes.customizeModal && !nodes.customizeModal.classList.contains("hidden")) {
    closeCustomizeModal();
  }
  state.activeScreen = screenName;
  for (const screen of nodes.screens) {
    screen.classList.toggle("active", screen.dataset.screen === screenName);
  }
  for (const button of nodes.navButtons) {
    button.classList.toggle("active", button.dataset.screen === screenName);
  }
  if (screenName === "orders") {
    loadOrders({ silent: true });
  }
  syncOrdersAutoRefresh();
  if (screenName === "cart") {
    window.requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "auto" });
    });
  }
}

function scrollToTarget(targetId) {
  if (!targetId) {
    return;
  }
  const target = document.getElementById(targetId);
  if (!target) {
    return;
  }
  switchScreen("home");
  window.requestAnimationFrame(() => {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function lockBodyScroll() {
  if (document.body.classList.contains("modal-open")) {
    return;
  }
  lockedScrollTop = window.scrollY || window.pageYOffset || 0;
  document.body.style.top = `-${lockedScrollTop}px`;
  document.body.classList.add("modal-open");
}

function unlockBodyScroll() {
  if (!document.body.classList.contains("modal-open")) {
    return;
  }
  document.body.classList.remove("modal-open");
  document.body.style.top = "";
  window.scrollTo(0, lockedScrollTop);
}

function openCustomizeModal(productId) {
  const product = getProductById(productId);
  if (!product) {
    return;
  }
  state.customize.productId = product.id;
  state.customize.sizeCode = getProductSizeOptions(product)[0]?.code || null;
  state.customize.addonCodes = [];
  renderCustomizeModal();
  nodes.customizeModal.classList.remove("hidden");
  lockBodyScroll();
}

function closeCustomizeModal() {
  nodes.customizeModal.classList.add("hidden");
  state.customize.productId = null;
  state.customize.sizeCode = null;
  state.customize.addonCodes = [];
  unlockBodyScroll();
}

function addItemToCart(item) {
  const normalized = sanitizeCartItems([item])[0];
  if (!normalized) {
    return;
  }
  const itemKey = getCartItemKey(normalized);
  const existing = state.cartItems.find((cartItem) => getCartItemKey(cartItem) === itemKey);
  if (existing) {
    existing.qty = Math.min(existing.qty + normalized.qty, 50);
  } else {
    state.cartItems.push(normalized);
  }
  persistState();
  renderCart();
}

function updateCartItem(itemKey, action) {
  const index = state.cartItems.findIndex((item) => getCartItemKey(item) === itemKey);
  if (index < 0) {
    return;
  }

  if (action === "remove") {
    state.cartItems.splice(index, 1);
  }
  if (action === "increase") {
    state.cartItems[index].qty = Math.min(state.cartItems[index].qty + 1, 50);
  }
  if (action === "decrease") {
    state.cartItems[index].qty -= 1;
    if (state.cartItems[index].qty <= 0) {
      state.cartItems.splice(index, 1);
    }
  }

  persistState();
  renderCart();
}

function applyMaxBonusSpend() {
  const maxBonusSpend = getMaxBonusSpendCents();
  state.bonusValue = maxBonusSpend > 0 ? formatMoneyInput(maxBonusSpend) : "";
  persistState();
  renderCart();
}

async function apiRequest(url, options = {}) {
  const config = { ...options };
  const headers = new Headers(config.headers || {});
  const initData = getTelegramInitData();
  if (initData && !headers.has("X-Telegram-Init-Data")) {
    headers.set("X-Telegram-Init-Data", initData);
  }
  if (config.body && !(config.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (config.body && headers.get("Content-Type")?.includes("application/json") && typeof config.body !== "string") {
    config.body = JSON.stringify(config.body);
  }
  config.headers = headers;

  let response;
  try {
    response = await fetch(url, config);
  } catch {
    throw new Error("Не удалось выполнить запрос. Проверьте подключение.");
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json().catch(() => ({}))
    : await response.text().catch(() => "");

  if (!response.ok) {
    const detail = typeof payload === "object" && payload && "detail" in payload
      ? payload.detail
      : "Не удалось выполнить запрос.";
    const error = new Error(getApiErrorMessage(detail));
    error.status = response.status;
    throw error;
  }

  return payload;
}

async function ensureSession() {
  const initData = getTelegramInitData();
  if (!initData) {
    return;
  }
  await apiRequest("/api/auth/telegram", {
    method: "POST",
    body: { init_data: initData },
  });
}

async function loadBootstrap() {
  const data = await apiRequest("/api/bootstrap");
  applyBootstrap(data);
}

async function refreshMe() {
  state.me = await apiRequest("/api/me");
  renderTopLevel();
  renderCart();
}

async function loadOrders({ silent = false } = {}) {
  if (state.ordersRequestInFlight) {
    return;
  }
  state.ordersRequestInFlight = true;
  const previousSignature = getOrdersSignature(state.orders);
  try {
    state.orders = await apiRequest("/api/orders/me");
    renderOrders();
    syncOrdersAutoRefresh();
    const nextSignature = getOrdersSignature(state.orders);
    if (previousSignature && nextSignature !== previousSignature) {
      await refreshMe();
    }
  } catch (error) {
    if (!silent) {
      notifyUser(error.message);
    }
  } finally {
    state.ordersRequestInFlight = false;
  }
}

async function cancelOrder(orderId) {
  try {
    await apiRequest(`/api/orders/${orderId}/cancel`, { method: "POST" });
    await refreshMe();
    await loadOrders();
    notifyUser("Заказ отменен.");
  } catch (error) {
    notifyUser(error.message);
  }
}

async function saveProfile() {
  clearMessage(nodes.profileMessage);
  nodes.saveProfileButton.disabled = true;
  try {
    state.me = await apiRequest("/api/me/profile", {
      method: "PUT",
      body: {
        full_name: nodes.nameInput.value.trim() || null,
      },
    });
    syncFormInputs();
    renderTopLevel();
    showMessage(nodes.profileMessage, "Имя сохранено.");
  } catch (error) {
    showMessage(nodes.profileMessage, error.message, "error");
  } finally {
    nodes.saveProfileButton.disabled = false;
  }
}

async function waitForPhoneSync() {
  for (let attempt = 0; attempt < PHONE_SYNC_ATTEMPTS; attempt += 1) {
    await sleep(PHONE_SYNC_DELAY_MS);
    try {
      const me = await apiRequest("/api/me");
      state.me = me;
      if (me.phone) {
        renderTopLevel();
        return true;
      }
    } catch {
      // Ignore transient sync errors here and continue polling.
    }
  }
  return false;
}

function requestTelegramPhone({ silent = false } = {}) {
  const tg = getTelegramWebApp();
  if (!tg?.requestContact) {
    if (!silent) {
      showMessage(nodes.profileMessage, "В этой версии Telegram нельзя запросить номер автоматически.", "error");
    }
    return;
  }
  if (state.phoneRequestInFlight) {
    return;
  }

  clearMessage(nodes.profileMessage);
  state.phoneRequestInFlight = true;
  tg.requestContact(async (requestSent) => {
    state.phoneRequestInFlight = false;
    if (!requestSent) {
      if (!silent) {
        showMessage(nodes.profileMessage, "Запрос телефона отменен.", "error");
      }
      return;
    }

    showMessage(nodes.profileMessage, "Запросили номер в Telegram. Подождите пару секунд.");
    const synced = await waitForPhoneSync();
    if (synced) {
      renderAll();
      showMessage(nodes.profileMessage, "Телефон подтвержден.");
      return;
    }

    showMessage(nodes.profileMessage, "Телефон еще не пришел. Нажмите кнопку еще раз.", "error");
  });
}

function maybeAutoRequestPhone() {
  if (state.autoPhonePromptDone || state.me?.phone) {
    return;
  }
  state.autoPhonePromptDone = true;
  requestTelegramPhone({ silent: true });
}

async function checkout() {
  clearMessage(nodes.orderMessage);

  if (!state.cartItems.length) {
    showMessage(nodes.orderMessage, "Корзина пустая.", "error");
    return;
  }
  if (!state.me?.phone) {
    switchScreen("profile");
    showMessage(nodes.profileMessage, "Сначала подтвердите телефон через Telegram.", "error");
    requestTelegramPhone();
    return;
  }
  if (!state.me?.full_name) {
    switchScreen("profile");
    showMessage(nodes.profileMessage, "Сначала укажите имя для заказа.", "error");
    return;
  }
  const bonusState = getBonusSpendState();
  if (!bonusState.isValid) {
    showMessage(nodes.orderMessage, bonusState.error, "error");
    renderCart();
    return;
  }

  nodes.checkoutButton.disabled = true;
  try {
    const order = await apiRequest("/api/orders", {
      method: "POST",
      body: {
        order_type: "pickup",
        consumption_place: state.consumptionPlace,
        pickup_time: getPickupRequestValue(),
        use_bonus_cents: bonusState.applied,
        promo_code: state.promoCode.trim() || null,
        note: state.note.trim() || null,
        items: state.cartItems.map((item) => ({
          product_id: item.product_id,
          qty: item.qty,
          size_code: item.size_code,
          addon_codes: item.addon_codes,
        })),
      },
    });

    state.cartItems = [];
    state.promoCode = "";
    state.bonusValue = "";
    state.note = "";
    syncFormInputs();
    persistState();
    renderCart();
    await refreshMe();
    await loadOrders();
    switchScreen("orders");
    notifyUser(`Заказ №${order.order_number} оформлен.`);
  } catch (error) {
    showMessage(nodes.orderMessage, error.message, "error");
  } finally {
    nodes.checkoutButton.disabled = false;
  }
}

function handleDocumentClick(event) {
  const switchButton = event.target.closest("[data-switch-screen]");
  if (switchButton) {
    switchScreen(switchButton.dataset.switchScreen);
    return;
  }

  const scrollButton = event.target.closest("[data-scroll-target]");
  if (scrollButton) {
    scrollToTarget(scrollButton.dataset.scrollTarget);
    return;
  }

  const navButton = event.target.closest(".nav-item[data-screen]");
  if (navButton) {
    switchScreen(navButton.dataset.screen);
    return;
  }

  const categoryButton = event.target.closest("[data-category-select]");
  if (categoryButton) {
    state.selectedCategorySlug = categoryButton.dataset.categorySelect || "all";
    persistState();
    renderCategories();
    renderProducts();
    return;
  }

  const pickupButton = event.target.closest("[data-pickup-offset]");
  if (pickupButton) {
    state.pickupMode = "preset";
    state.selectedPickupOffset = Number(pickupButton.dataset.pickupOffset);
    state.customPickupText = "";
    persistState();
    renderPickupControls();
    return;
  }

  const consumptionButton = event.target.closest("[data-consumption-place]");
  if (consumptionButton) {
    state.consumptionPlace = consumptionButton.dataset.consumptionPlace === "dine_in" ? "dine_in" : "takeaway";
    persistState();
    renderPickupControls();
    return;
  }

  const productButton = event.target.closest("[data-product-action]");
  if (productButton) {
    const product = getProductById(productButton.dataset.productAction);
    if (!product) {
      return;
    }
    const sizeOptions = getProductSizeOptions(product);
    const addonOptions = getProductAddonOptions(product);
    if (sizeOptions.length > 1 || addonOptions.length > 0) {
      openCustomizeModal(product.id);
      return;
    }
    addItemToCart({
      product_id: product.id,
      qty: 1,
      size_code: sizeOptions[0]?.code || null,
      addon_codes: [],
    });
    return;
  }

  const sizeButton = event.target.closest("[data-size-option]");
  if (sizeButton) {
    state.customize.sizeCode = sizeButton.dataset.sizeOption || null;
    renderCustomizeModal();
    return;
  }

  const addonButton = event.target.closest("[data-addon-option]");
  if (addonButton) {
    const code = addonButton.dataset.addonOption;
    if (!code) {
      return;
    }
    if (state.customize.addonCodes.includes(code)) {
      state.customize.addonCodes = state.customize.addonCodes.filter((item) => item !== code);
    } else {
      state.customize.addonCodes = [...state.customize.addonCodes, code];
    }
    renderCustomizeModal();
    return;
  }

  const cartButton = event.target.closest("[data-cart-action]");
  if (cartButton) {
    updateCartItem(cartButton.dataset.cartKey, cartButton.dataset.cartAction);
    return;
  }

  const cancelButton = event.target.closest("[data-order-cancel]");
  if (cancelButton) {
    const confirmed = window.confirm("Отменить этот заказ?");
    if (!confirmed) {
      return;
    }
    cancelOrder(cancelButton.dataset.orderCancel);
  }
}

function bindEvents() {
  document.addEventListener("click", handleDocumentClick);

  nodes.customTimeInput.addEventListener("input", () => {
    state.customPickupText = nodes.customTimeInput.value;
    state.pickupMode = nodes.customTimeInput.value.trim() ? "custom" : "preset";
    persistState();
    renderPickupControls();
  });

  nodes.productSearchInput.addEventListener("input", () => {
    state.searchQuery = nodes.productSearchInput.value;
    persistState();
    renderProducts();
  });

  nodes.promoInput.addEventListener("input", () => {
    state.promoCode = nodes.promoInput.value.toUpperCase();
    nodes.promoInput.value = state.promoCode;
    persistState();
  });

  nodes.bonusInput.addEventListener("input", () => {
    state.bonusValue = nodes.bonusInput.value;
    persistState();
    renderCart();
  });
  nodes.bonusMaxButton.addEventListener("click", applyMaxBonusSpend);

  nodes.noteInput.addEventListener("input", () => {
    state.note = nodes.noteInput.value;
    persistState();
  });

  nodes.checkoutButton.addEventListener("click", checkout);
  nodes.saveProfileButton.addEventListener("click", saveProfile);
  nodes.requestPhoneButton.addEventListener("click", () => requestTelegramPhone());

  nodes.closeCustomizeButton.addEventListener("click", closeCustomizeModal);
  nodes.customizeModal.addEventListener("click", (event) => {
    if (event.target === nodes.customizeModal) {
      closeCustomizeModal();
    }
  });
  nodes.addConfiguredProductButton.addEventListener("click", () => {
    if (!state.customize.productId) {
      return;
    }
    addItemToCart({
      product_id: state.customize.productId,
      qty: 1,
      size_code: state.customize.sizeCode,
      addon_codes: state.customize.addonCodes,
    });
    closeCustomizeModal();
  });

  document.addEventListener("keydown", (event) => {
    const productCard = event.target instanceof Element
      ? event.target.closest(".product-card[data-product-action]")
      : null;
    if (productCard && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      productCard.click();
      return;
    }
    if (event.key === "Escape" && !nodes.customizeModal.classList.contains("hidden")) {
      closeCustomizeModal();
    }
  });

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && (state.activeScreen === "orders" || hasLiveOrders())) {
      loadOrders({ silent: true });
    }
    if (document.hidden) {
      if (bannerRotationTimer) {
        window.clearInterval(bannerRotationTimer);
        bannerRotationTimer = null;
      }
      syncOrdersAutoRefresh();
      return;
    }
    if (state.activeScreen === "home") {
      renderBanners();
    }
    syncOrdersAutoRefresh();
  });
}

async function init() {
  const tg = getTelegramWebApp();
  tg?.ready?.();
  tg?.expand?.();

  bindEvents();
  switchScreen("home");

  try {
    await ensureSession().catch((error) => {
      if (error.status !== 401 && error.status !== 400) {
        throw error;
      }
    });
    await loadBootstrap();
    restoreStateFromStorage();
    renderAll();
    await loadOrders();
    maybeAutoRequestPhone();
  } catch (error) {
    showMessage(nodes.profileMessage, error.message, "error");
    notifyUser(error.message);
  }
}

window.addEventListener("DOMContentLoaded", init);


