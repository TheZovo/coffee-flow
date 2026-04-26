const state = {
  banners: [],
  baristas: [],
  baristaShifts: [],
  categories: [],
  loyaltySettings: {
    classic_category_slug: "coffee",
    classic_category_slugs: ["coffee"],
    paid_items_per_reward: 5,
    bonus_enabled: true,
    bonus_earn_percent: 5,
    bonus_redeem_enabled: true,
    bonus_redeem_max_percent: 100,
  },
  appSettings: {},
  reminderSettings: {
    inactive_reminder_enabled: false,
    inactive_reminder_days: 30,
    inactive_reminder_send_time: "12:00",
    inactive_reminder_text: "",
    inactive_reminder_last_run_at: null,
  },
  analytics: null,
  products: [],
  filterCategory: "all",
  activeTab: "programs",
  activeSubtabs: {
    programs: "loyalty",
    storefront: "banners",
    catalog: "categories",
    team: "baristas",
    reminders: "",
    analytics: "",
    bot: "start",
  },
};

const WEEKDAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const ADMIN_TAB_SUBTABS = {
  programs: ["loyalty", "bonus"],
  storefront: ["banners"],
  catalog: ["categories", "products"],
  team: ["baristas", "shifts"],
  reminders: [],
  analytics: [],
  bot: ["start", "contacts", "ordering", "customer-statuses", "barista", "order-templates"],
};

const DEFAULT_ADMIN_SUBTABS = {
  programs: "loyalty",
  storefront: "banners",
  catalog: "categories",
  team: "baristas",
  reminders: "",
  analytics: "",
  bot: "start",
};

const MAX_IMAGE_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024;
const ALLOWED_IMAGE_MIME_TYPES = new Set([
  "image/png",
  "image/jpeg",
  "image/webp",
  "image/svg+xml",
  "image/gif",
]);
const ALLOWED_IMAGE_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]);

const APP_SETTINGS_FIELDS = [
  "miniapp_button_text",
  "customer_start_text",
  "customer_app_text",
  "customer_help_text",
  "customer_contact_request_text",
  "customer_phone_error_text",
  "customer_phone_saved_text",
  "customer_order_created_text",
  "customer_status_in_progress_text",
  "customer_status_ready_text",
  "customer_status_en_route_text",
  "customer_status_completed_text",
  "customer_status_cancelled_text",
  "barista_start_text",
  "barista_login_invalid_text",
  "barista_login_success_text",
  "barista_logout_text",
  "barista_access_denied_text",
  "barista_queue_empty_text",
  "barista_queue_summary_text",
  "barista_order_usage_text",
  "barista_order_not_found_text",
  "barista_today_empty_text",
  "barista_today_summary_text",
  "barista_user_not_found_text",
  "barista_invalid_order_id_text",
  "barista_unknown_action_text",
  "barista_order_closed_text",
  "barista_delivery_only_status_text",
  "barista_order_reload_error_text",
  "barista_status_updated_text",
  "pickup_asap_text",
  "order_type_pickup_label",
  "order_type_delivery_label",
  "order_status_new_label",
  "order_status_in_progress_label",
  "order_status_ready_label",
  "order_status_en_route_label",
  "order_status_completed_label",
  "order_status_cancelled_label",
  "order_contact_name_fallback",
  "order_contact_phone_fallback",
  "order_empty_items_text",
  "order_promo_label",
  "order_loyalty_label",
  "order_bonus_spent_label",
  "order_bonus_earned_label",
  "order_note_label",
  "order_delivery_address_label",
  "order_delivery_comment_label",
  "barista_action_take_text",
  "barista_action_ready_text",
  "barista_action_route_text",
  "barista_action_done_text",
  "barista_action_cancel_text",
  "barista_order_card_text",
  "barista_new_order_text",
];

const nodes = {
  authCard: document.getElementById("authCard"),
  dashboard: document.getElementById("dashboard"),
  authMessage: document.getElementById("authMessage"),
  dashboardMessage: document.getElementById("dashboardMessage"),
  adminTabs: Array.from(document.querySelectorAll("[data-admin-tab]")),
  adminPanels: Array.from(document.querySelectorAll("[data-admin-panel]")),
  adminSubtabs: Array.from(document.querySelectorAll("[data-admin-subtab]")),
  adminSubpanels: Array.from(document.querySelectorAll("[data-admin-subpanel]")),
  loginForm: document.getElementById("loginForm"),
  secretInput: document.getElementById("secretInput"),
  logoutButton: document.getElementById("logoutButton"),
  categoryCount: document.getElementById("categoryCount"),
  productCount: document.getElementById("productCount"),
  bannerCount: document.getElementById("bannerCount"),
  activeProductCount: document.getElementById("activeProductCount"),
  loyaltyForm: document.getElementById("loyaltyForm"),
  loyaltyMessage: document.getElementById("loyaltyMessage"),
  loyaltyPreviewText: document.getElementById("loyaltyPreviewText"),
  appSettingsForm: document.getElementById("appSettingsForm"),
  appSettingsMessage: document.getElementById("appSettingsMessage"),
  reminderForm: document.getElementById("reminderForm"),
  reminderMessage: document.getElementById("reminderMessage"),
  reminderPreview: document.getElementById("reminderPreview"),
  resetAppSettingsButton: document.getElementById("resetAppSettingsButton"),
  baristaList: document.getElementById("baristaList"),
  shiftList: document.getElementById("shiftList"),
  categoryList: document.getElementById("categoryList"),
  productList: document.getElementById("productList"),
  bannerList: document.getElementById("bannerList"),
  productFilterCategory: document.getElementById("productFilterCategory"),
  resetLoyaltyButton: document.getElementById("resetLoyaltyButton"),
  newBaristaButton: document.getElementById("newBaristaButton"),
  newShiftButton: document.getElementById("newShiftButton"),
  newCategoryButton: document.getElementById("newCategoryButton"),
  newProductButton: document.getElementById("newProductButton"),
  newBannerButton: document.getElementById("newBannerButton"),
  resetBaristaButton: document.getElementById("resetBaristaButton"),
  resetShiftButton: document.getElementById("resetShiftButton"),
  resetCategoryButton: document.getElementById("resetCategoryButton"),
  resetProductButton: document.getElementById("resetProductButton"),
  resetBannerButton: document.getElementById("resetBannerButton"),
  addSizeButton: document.getElementById("addSizeButton"),
  addAddonButton: document.getElementById("addAddonButton"),
  baristaForm: document.getElementById("baristaForm"),
  shiftForm: document.getElementById("shiftForm"),
  categoryForm: document.getElementById("categoryForm"),
  productForm: document.getElementById("productForm"),
  bannerForm: document.getElementById("bannerForm"),
  baristaMessage: document.getElementById("baristaMessage"),
  shiftMessage: document.getElementById("shiftMessage"),
  categoryMessage: document.getElementById("categoryMessage"),
  productMessage: document.getElementById("productMessage"),
  bannerMessage: document.getElementById("bannerMessage"),
  productSizeOptions: document.getElementById("productSizeOptions"),
  productAddonOptions: document.getElementById("productAddonOptions"),
  productImageFile: document.getElementById("productImageFile"),
  productImagePath: document.getElementById("productImagePath"),
  productImagePreview: document.getElementById("productImagePreview"),
  clearProductImageButton: document.getElementById("clearProductImageButton"),
  bannerImageFile: document.getElementById("bannerImageFile"),
  bannerImagePath: document.getElementById("bannerImagePath"),
  bannerImagePreview: document.getElementById("bannerImagePreview"),
  clearBannerImageButton: document.getElementById("clearBannerImageButton"),
  analyticsDateFrom: document.getElementById("analyticsDateFrom"),
  analyticsDateTo: document.getElementById("analyticsDateTo"),
  analyticsLoadButton: document.getElementById("analyticsLoadButton"),
  analyticsExportCsvButton: document.getElementById("analyticsExportCsvButton"),
  analyticsExportXlsxButton: document.getElementById("analyticsExportXlsxButton"),
  analyticsMessage: document.getElementById("analyticsMessage"),
  analyticsKpis: document.getElementById("analyticsKpis"),
  analyticsTopProducts: document.getElementById("analyticsTopProducts"),
  analyticsTopCategories: document.getElementById("analyticsTopCategories"),
  analyticsPromoUsage: document.getElementById("analyticsPromoUsage"),
  analyticsStatusBreakdown: document.getElementById("analyticsStatusBreakdown"),
  analyticsDailyRevenue: document.getElementById("analyticsDailyRevenue"),
  analyticsRangeButtons: Array.from(document.querySelectorAll("[data-analytics-range]")),
};

const baristaFormNodes = {
  id: document.getElementById("baristaId"),
  fullName: document.getElementById("baristaFullName"),
  username: document.getElementById("baristaUsername"),
  isActive: document.getElementById("baristaIsActive"),
};

const shiftFormNodes = {
  id: document.getElementById("shiftId"),
  userId: document.getElementById("shiftBaristaId"),
  weekday: document.getElementById("shiftWeekday"),
  startTime: document.getElementById("shiftStartTime"),
  endTime: document.getElementById("shiftEndTime"),
  note: document.getElementById("shiftNote"),
  isActive: document.getElementById("shiftIsActive"),
};

const categoryFormNodes = {
  id: document.getElementById("categoryId"),
  name: document.getElementById("categoryName"),
  slug: document.getElementById("categorySlug"),
  sortOrder: document.getElementById("categorySortOrder"),
  isActive: document.getElementById("categoryIsActive"),
};

const loyaltyFormNodes = {
  categoryOptions: document.getElementById("loyaltyCategoryOptions"),
  paidItemsPerReward: document.getElementById("loyaltyPaidItemsPerReward"),
  bonusEnabled: document.getElementById("bonusEnabled"),
  bonusEarnPercent: document.getElementById("bonusEarnPercent"),
  bonusRedeemEnabled: document.getElementById("bonusRedeemEnabled"),
  bonusRedeemMaxPercent: document.getElementById("bonusRedeemMaxPercent"),
};

const reminderFormNodes = {
  enabled: document.getElementById("reminderEnabled"),
  days: document.getElementById("reminderDays"),
  sendTime: document.getElementById("reminderSendTime"),
  text: document.getElementById("reminderText"),
};

const productFormNodes = {
  id: document.getElementById("productId"),
  categoryId: document.getElementById("productCategory"),
  productType: document.getElementById("productType"),
  name: document.getElementById("productName"),
  badge: document.getElementById("productBadge"),
  imageUrl: document.getElementById("productImageUrl"),
  description: document.getElementById("productDescription"),
  composition: document.getElementById("productComposition"),
  caloriesKcal: document.getElementById("productCaloriesKcal"),
  sortOrder: document.getElementById("productSortOrder"),
  isActive: document.getElementById("productIsActive"),
};

const bannerFormNodes = {
  id: document.getElementById("bannerId"),
  title: document.getElementById("bannerTitle"),
  subtitle: document.getElementById("bannerSubtitle"),
  description: document.getElementById("bannerDescription"),
  imageUrl: document.getElementById("bannerImageUrl"),
  sortOrder: document.getElementById("bannerSortOrder"),
  isActive: document.getElementById("bannerIsActive"),
};

let categorySlugTouched = false;

function showMessage(node, text, kind = "success") {
  if (!node) {
    return;
  }
  node.textContent = text;
  node.classList.remove("hidden", "is-success", "is-error");
  node.classList.add(kind === "error" ? "is-error" : "is-success");
}

function clearMessage(node) {
  if (!node) {
    return;
  }
  node.textContent = "";
  node.classList.add("hidden");
  node.classList.remove("is-success", "is-error");
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

function getFieldLabel(control) {
  if (!control) {
    return "поле";
  }
  const labelNode = control.closest("label")?.querySelector("span");
  if (labelNode?.textContent?.trim()) {
    return labelNode.textContent.trim();
  }
  return control.getAttribute("aria-label")
    || control.getAttribute("placeholder")
    || control.name
    || control.id
    || "поле";
}

function getConstraintErrorMessage(control) {
  const label = getFieldLabel(control);
  if (!control?.validity) {
    return `Проверьте поле "${label}".`;
  }
  if (control.validity.valueMissing) {
    return `Заполните поле "${label}".`;
  }
  if (control.validity.tooShort) {
    return `Поле "${label}" заполнено слишком коротко.`;
  }
  if (control.validity.tooLong) {
    return `Поле "${label}" превышает допустимую длину.`;
  }
  if (control.validity.rangeUnderflow) {
    return `Поле "${label}" не должно быть меньше ${control.min}.`;
  }
  if (control.validity.rangeOverflow) {
    return `Поле "${label}" не должно быть больше ${control.max}.`;
  }
  if (control.validity.typeMismatch || control.validity.badInput || control.validity.stepMismatch) {
    return `Проверьте значение поля "${label}".`;
  }
  if (control.validity.patternMismatch) {
    return `Поле "${label}" заполнено в неверном формате.`;
  }
  return `Проверьте поле "${label}".`;
}

function ensureFormValidity(form, messageNode) {
  if (!form || form.checkValidity()) {
    return true;
  }
  const invalidControl = form.querySelector(":invalid");
  showMessage(messageNode, getConstraintErrorMessage(invalidControl), "error");
  invalidControl?.reportValidity?.();
  invalidControl?.focus?.();
  return false;
}

function bindMessageReset(form, messageNode) {
  if (!form || !messageNode) {
    return;
  }
  const reset = () => clearMessage(messageNode);
  form.addEventListener("input", reset);
  form.addEventListener("change", reset);
}

function handleExpiredAdminSession(message = "Сессия истекла. Войдите снова.") {
  setAuthenticated(false);
  clearMessage(nodes.dashboardMessage);
  if (message) {
    showMessage(nodes.authMessage, message, "error");
  } else {
    clearMessage(nodes.authMessage);
  }
  nodes.secretInput?.focus();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function slugify(value) {
  return value
    .trim()
    .toLowerCase()
    .replaceAll("_", "-")
    .replace(/\s+/g, "-")
    .replace(/[^\w-]+/g, "")
    .replace(/-{2,}/g, "-")
    .replace(/^-+|-+$/g, "");
}

function formatMoney(cents) {
  return `${(Number(cents || 0) / 100).toFixed(2)} BYN`;
}

function formatDateTime(value) {
  if (!value) {
    return "Не указано";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Не указано";
  }
  return parsed.toLocaleString("ru-BY", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(value) {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }
  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDateTimeForInput(value) {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }
  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  const hours = String(parsed.getHours()).padStart(2, "0");
  const minutes = String(parsed.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function parseDateTimeInput(value, label) {
  const normalized = String(value ?? "").trim();
  if (!normalized) {
    throw new Error(`Укажите "${label}".`);
  }
  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) {
    throw new Error(`Поле "${label}" заполнено в неверном формате.`);
  }
  return parsed.toISOString();
}

function getBaristaDisplayName(barista) {
  if (!barista) {
    return "Бариста";
  }
  return barista.full_name || barista.username || `Бариста #${barista.id}`;
}

function getBaristaBindingLabel(barista) {
  if (!barista) {
    return "Не привязан";
  }
  if (barista.telegram_id) {
    return `Привязан: ${barista.telegram_id}`;
  }
  if (barista.username) {
    return "Ожидает первый вход по username";
  }
  return "Ожидает первый вход по имени";
}

function defaultProgramSettings() {
  return {
    classic_category_slug: "coffee",
    classic_category_slugs: ["coffee"],
    paid_items_per_reward: 5,
    bonus_enabled: true,
    bonus_earn_percent: 5,
    bonus_redeem_enabled: true,
    bonus_redeem_max_percent: 100,
  };
}

function defaultReminderSettings() {
  return {
    inactive_reminder_enabled: false,
    inactive_reminder_days: 30,
    inactive_reminder_send_time: "12:00",
    inactive_reminder_text: "",
    inactive_reminder_last_run_at: null,
  };
}

function normalizeLoyaltyCategorySlugs(values) {
  const rawValues = Array.isArray(values)
    ? values
    : String(values ?? "").split(/[,\n;]/);
  const normalized = [];
  const seen = new Set();
  rawValues.forEach((value) => {
    const slug = slugify(String(value ?? ""));
    if (!slug || seen.has(slug)) {
      return;
    }
    seen.add(slug);
    normalized.push(slug);
  });
  return normalized.length ? normalized : ["coffee"];
}

function getCurrentLoyaltyCategorySlugs() {
  if (!loyaltyFormNodes.categoryOptions) {
    return [];
  }
  return Array.from(
    loyaltyFormNodes.categoryOptions.querySelectorAll('input[name="loyaltyCategorySlugs"]:checked'),
  ).map((control) => control.value);
}

function formatCategoryNamesList(labels) {
  if (!labels.length) {
    return "выбранной категории";
  }
  if (labels.length === 1) {
    return `категории "${labels[0]}"`;
  }
  return `категорий "${labels.join('", "')}"`;
}

function defaultAppSettings() {
  return Object.fromEntries(APP_SETTINGS_FIELDS.map((fieldName) => [fieldName, ""]));
}

function getAppSettingsControl(fieldName) {
  return nodes.appSettingsForm?.elements?.namedItem(fieldName) || null;
}

function fillAppSettingsForm(appSettings = state.appSettings) {
  state.appSettings = {
    ...defaultAppSettings(),
    ...(appSettings || {}),
  };
  APP_SETTINGS_FIELDS.forEach((fieldName) => {
    const control = getAppSettingsControl(fieldName);
    if (control && "value" in control) {
      control.value = state.appSettings[fieldName] || "";
    }
  });
  clearMessage(nodes.appSettingsMessage);
}

function buildAppSettingsPayload() {
  const payload = {};
  APP_SETTINGS_FIELDS.forEach((fieldName) => {
    const control = getAppSettingsControl(fieldName);
    payload[fieldName] = control && "value" in control ? String(control.value ?? "") : "";
  });
  return payload;
}

function resetAppSettingsForm() {
  fillAppSettingsForm(state.appSettings);
}

function fillReminderForm(reminderSettings = state.reminderSettings) {
  state.reminderSettings = {
    ...defaultReminderSettings(),
    ...(reminderSettings || {}),
  };
  reminderFormNodes.enabled.checked = Boolean(state.reminderSettings.inactive_reminder_enabled);
  reminderFormNodes.days.value = String(Math.max(1, Number(state.reminderSettings.inactive_reminder_days || 30)));
  reminderFormNodes.sendTime.value = state.reminderSettings.inactive_reminder_send_time || "12:00";
  reminderFormNodes.text.value = state.reminderSettings.inactive_reminder_text || "";
  renderReminderPreview();
  clearMessage(nodes.reminderMessage);
}

function buildReminderPayload() {
  return {
    inactive_reminder_enabled: reminderFormNodes.enabled.checked,
    inactive_reminder_days: parsePositiveInteger(reminderFormNodes.days.value, "Неактивен, дней", { max: 3650 }),
    inactive_reminder_send_time: String(reminderFormNodes.sendTime.value || "12:00"),
    inactive_reminder_text: String(reminderFormNodes.text.value || ""),
  };
}

function renderReminderPreview() {
  if (!nodes.reminderPreview) {
    return;
  }
  if (!reminderFormNodes.enabled.checked) {
    nodes.reminderPreview.textContent = "Напоминания выключены.";
    return;
  }
  nodes.reminderPreview.textContent = `Напоминание уйдет пользователям без заказов ${reminderFormNodes.days.value || 30} дн. в ${reminderFormNodes.sendTime.value || "12:00"}.`;
}

function setAuthenticated(isAuthenticated) {
  nodes.authCard.classList.toggle("hidden", isAuthenticated);
  nodes.dashboard.classList.toggle("hidden", !isAuthenticated);
}

function getAdminTabSubtabs(tabName) {
  return ADMIN_TAB_SUBTABS[tabName] || [];
}

function getDefaultAdminSubtab(tabName) {
  return DEFAULT_ADMIN_SUBTABS[tabName] || getAdminTabSubtabs(tabName)[0] || "";
}

function getCurrentAdminSubtab(tabName) {
  const subtab = state.activeSubtabs[tabName];
  return getAdminTabSubtabs(tabName).includes(subtab) ? subtab : getDefaultAdminSubtab(tabName);
}

function switchAdminSubtab(tabName, subtabName) {
  const normalizedTab = ADMIN_TAB_SUBTABS[tabName] ? tabName : "programs";
  const availableSubtabs = getAdminTabSubtabs(normalizedTab);
  const normalizedSubtab = availableSubtabs.includes(subtabName)
    ? subtabName
    : getDefaultAdminSubtab(normalizedTab);

  state.activeSubtabs[normalizedTab] = normalizedSubtab;
  nodes.adminSubtabs.forEach((button) => {
    const isActive = button.dataset.adminSubtabGroup === normalizedTab
      && button.dataset.adminSubtab === normalizedSubtab;
    button.classList.toggle("active", isActive);
  });
  nodes.adminSubpanels.forEach((panel) => {
    const isActive = panel.dataset.adminSubpanelGroup === normalizedTab
      && panel.dataset.adminSubpanel === normalizedSubtab;
    panel.classList.toggle("active", isActive);
  });
}

function switchAdminTab(tabName, subtabName = null) {
  state.activeTab = ADMIN_TAB_SUBTABS[tabName] ? tabName : "programs";
  nodes.adminTabs.forEach((button) => {
    button.classList.toggle("active", button.dataset.adminTab === state.activeTab);
  });
  nodes.adminPanels.forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.adminPanel === state.activeTab);
  });
  switchAdminSubtab(state.activeTab, subtabName || getCurrentAdminSubtab(state.activeTab));
  if (state.activeTab === "analytics" && !state.analytics) {
    loadAnalytics();
  }
}

async function apiRequest(url, options = {}) {
  const config = { ...options };
  const headers = new Headers(config.headers || {});

  if (config.body && !(config.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  config.headers = headers;

  if (config.body && headers.get("Content-Type")?.includes("application/json") && typeof config.body !== "string") {
    config.body = JSON.stringify(config.body);
  }

  let response;
  try {
    response = await fetch(url, config);
  } catch {
    throw new Error("Не удалось связаться с сервером. Проверьте подключение.");
  }
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json().catch(() => ({}))
    : await response.text().catch(() => "");

  if (!response.ok) {
    const error = new Error(
      getApiErrorMessage(
        typeof payload === "object" && payload && "detail" in payload
          ? payload.detail
          : payload,
      ),
    );
    error.status = response.status;
    throw error;
  }

  return payload;
}

function parseOptionalInteger(value, label, options = {}) {
  const { min = 0, max = null } = options;
  const normalized = String(value ?? "").trim();
  if (!normalized) {
    return null;
  }
  const parsed = Number(normalized);
  if (!Number.isInteger(parsed) || parsed < min) {
    if (min <= 0) {
      throw new Error(`Поле "${label}" должно быть целым неотрицательным числом.`);
    }
    throw new Error(`Поле "${label}" должно быть целым числом не меньше ${min}.`);
  }
  if (max != null && parsed > max) {
    throw new Error(`Поле "${label}" не должно быть больше ${max}.`);
  }
  return parsed;
}

function parsePositiveInteger(value, label, options = {}) {
  const { max = null } = options;
  const parsed = parseOptionalInteger(value, label, { min: 1, max });
  if (parsed == null || parsed < 1) {
    throw new Error(`Поле "${label}" должно быть числом больше нуля.`);
  }
  return parsed;
}

function parseMoneyToCents(value, label, options = {}) {
  const { maxCents = 1000000 } = options;
  const normalized = String(value ?? "").trim().replace(",", ".");
  if (!normalized) {
    throw new Error(`Укажите значение для поля "${label}".`);
  }
  const parsed = Number(normalized);
  if (!Number.isFinite(parsed) || parsed < 0) {
    throw new Error(`Поле "${label}" должно быть неотрицательным числом.`);
  }
  const cents = Math.round(parsed * 100);
  if (cents > maxCents) {
    throw new Error(`Поле "${label}" не должно быть больше ${formatMoney(maxCents)}.`);
  }
  return cents;
}

function getFileExtension(filename) {
  const normalized = String(filename ?? "").trim().toLowerCase();
  const lastDotIndex = normalized.lastIndexOf(".");
  if (lastDotIndex < 0) {
    return "";
  }
  return normalized.slice(lastDotIndex);
}

function validateImageFile(file) {
  if (!file) {
    return;
  }
  const extension = getFileExtension(file.name);
  const mimeType = String(file.type || "").trim().toLowerCase();
  if (file.size <= 0) {
    throw new Error("Файл пустой.");
  }
  if (file.size > MAX_IMAGE_UPLOAD_SIZE_BYTES) {
    throw new Error("Изображение не должно быть больше 5 МБ.");
  }
  if (!ALLOWED_IMAGE_EXTENSIONS.has(extension) && !ALLOWED_IMAGE_MIME_TYPES.has(mimeType)) {
    throw new Error("Поддерживаются только PNG, JPG, WEBP, SVG и GIF.");
  }
}

function getUploadPathLabel(url) {
  const normalized = String(url ?? "").trim();
  return normalized || "Файл не выбран";
}

function applyUploadState({ url, hiddenInput, pathNode, previewNode, fileNode }) {
  hiddenInput.value = url || "";
  pathNode.textContent = getUploadPathLabel(url);
  previewNode.classList.toggle("hidden", !url);
  if (url) {
    previewNode.src = url;
  } else {
    previewNode.removeAttribute("src");
  }
  if (fileNode) {
    fileNode.value = "";
  }
}

async function uploadImage(file, messageNode, applyImageUrl, fileInput) {
  if (!file) {
    return;
  }
  clearMessage(messageNode);

  try {
    validateImageFile(file);

    const formData = new FormData();
    formData.append("file", file);

    showMessage(messageNode, "Загружаем изображение...");
    fileInput.disabled = true;
    const payload = await apiRequest("/api/admin/uploads/images", {
      method: "POST",
      body: formData,
    });
    applyImageUrl(payload.url);
    showMessage(messageNode, "Изображение загружено.");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(messageNode, error.message, "error");
  } finally {
    fileInput.disabled = false;
    fileInput.value = "";
  }
}

function createSizeOptionRow(option = {}) {
  return `
    <div class="config-row" data-option-kind="size">
      <input type="hidden" data-field="code" value="${escapeHtml(option.code || "")}" />
      <label class="field">
        <span>Название размера</span>
        <input type="text" data-field="name" maxlength="80" placeholder="Большой" value="${escapeHtml(option.name || "")}" />
      </label>
      <label class="field">
        <span>Граммовка / объем</span>
        <input type="text" data-field="volume_label" maxlength="40" placeholder="450 мл" value="${escapeHtml(option.volume_label || "")}" />
      </label>
      <label class="field">
        <span>Цена, BYN</span>
        <input type="number" data-field="price" min="0" max="10000" step="0.01" placeholder="5.90" value="${option.price_cents != null ? (Number(option.price_cents) / 100).toFixed(2) : ""}" />
      </label>
      <button class="ghost-button remove-option-button" type="button" data-remove-option="size">Удалить</button>
    </div>
  `;
}

function createAddonOptionRow(option = {}) {
  return `
    <div class="config-row" data-option-kind="addon">
      <input type="hidden" data-field="code" value="${escapeHtml(option.code || "")}" />
      <label class="field">
        <span>Название допа</span>
        <input type="text" data-field="name" maxlength="80" placeholder="Карамель" value="${escapeHtml(option.name || "")}" />
      </label>
      <label class="field">
        <span>Цена, BYN</span>
        <input type="number" data-field="price" min="0" max="10000" step="0.01" placeholder="0.70" value="${option.price_cents != null ? (Number(option.price_cents) / 100).toFixed(2) : ""}" />
      </label>
      <button class="ghost-button remove-option-button" type="button" data-remove-option="addon">Удалить</button>
    </div>
  `;
}

function renderSizeOptionRows(options = []) {
  nodes.productSizeOptions.innerHTML = options.length
    ? options.map((option) => createSizeOptionRow(option)).join("")
    : '<div class="config-empty">Размеры еще не настроены.</div>';
}

function renderAddonOptionRows(options = []) {
  nodes.productAddonOptions.innerHTML = options.length
    ? options.map((option) => createAddonOptionRow(option)).join("")
    : '<div class="config-empty">Допы еще не настроены.</div>';
}

function appendSizeOptionRow(option = {}) {
  if (nodes.productSizeOptions.querySelector(".config-empty")) {
    nodes.productSizeOptions.innerHTML = "";
  }
  nodes.productSizeOptions.insertAdjacentHTML("beforeend", createSizeOptionRow(option));
}

function appendAddonOptionRow(option = {}) {
  if (nodes.productAddonOptions.querySelector(".config-empty")) {
    nodes.productAddonOptions.innerHTML = "";
  }
  nodes.productAddonOptions.insertAdjacentHTML("beforeend", createAddonOptionRow(option));
}

function collectSizeOptions() {
  const rows = Array.from(nodes.productSizeOptions.querySelectorAll('.config-row[data-option-kind="size"]'));
  const result = rows.map((row) => {
    const name = row.querySelector('[data-field="name"]').value.trim();
    const volumeLabel = row.querySelector('[data-field="volume_label"]').value.trim();
    const priceValue = row.querySelector('[data-field="price"]').value.trim();
    const code = row.querySelector('[data-field="code"]').value.trim() || null;

    if (!name && !volumeLabel && !priceValue) {
      return null;
    }
    if (!name || !volumeLabel || !priceValue) {
      throw new Error("У каждого размера должны быть название, граммовка и цена.");
    }

    return {
      code,
      name,
      volume_label: volumeLabel,
      price_cents: parseMoneyToCents(priceValue, `Цена размера "${name}"`),
    };
  }).filter(Boolean);

  if (!result.length) {
    throw new Error("Добавьте хотя бы один размер с ценой.");
  }

  return result;
}

function collectAddonOptions() {
  const rows = Array.from(nodes.productAddonOptions.querySelectorAll('.config-row[data-option-kind="addon"]'));
  return rows.map((row) => {
    const name = row.querySelector('[data-field="name"]').value.trim();
    const priceValue = row.querySelector('[data-field="price"]').value.trim();
    const code = row.querySelector('[data-field="code"]').value.trim() || null;

    if (!name && !priceValue) {
      return null;
    }
    if (!name) {
      throw new Error("У каждого допа должно быть название.");
    }
    if (!priceValue) {
      throw new Error(`Укажите цену для допа "${name}".`);
    }

    return {
      code,
      name,
      price_cents: parseMoneyToCents(priceValue, `Цена допа "${name}"`),
    };
  }).filter(Boolean);
}

function buildCategoryPayload() {
  const name = categoryFormNodes.name.value.trim();
  const slug = categoryFormNodes.slug.value.trim();
  if (!name) {
    throw new Error("Укажите название категории.");
  }
  if (!slug) {
    throw new Error("Укажите slug категории.");
  }

    return {
      name,
      slug,
      sort_order: parseOptionalInteger(categoryFormNodes.sortOrder.value, "Порядок сортировки", { max: 10000 }) ?? 100,
      is_active: categoryFormNodes.isActive.checked,
    };
}

function buildProductPayload() {
  const name = productFormNodes.name.value.trim();
  const productType = productFormNodes.productType.value.trim();
  if (!name) {
    throw new Error("Укажите название товара.");
  }
  if (!productType) {
    throw new Error("Укажите тип продукции.");
  }

  const categoryIdValue = productFormNodes.categoryId.value;

  return {
    category_id: categoryIdValue ? Number(categoryIdValue) : null,
    product_type: productType,
    name,
    description: productFormNodes.description.value.trim() || null,
    composition: productFormNodes.composition.value.trim() || null,
    image_url: productFormNodes.imageUrl.value.trim() || null,
    badge: productFormNodes.badge.value.trim() || null,
    calories_kcal: parseOptionalInteger(productFormNodes.caloriesKcal.value, "Калорийность", { max: 10000 }),
    sort_order: parseOptionalInteger(productFormNodes.sortOrder.value, "Порядок сортировки", { max: 10000 }) ?? 100,
    is_active: productFormNodes.isActive.checked,
    size_options: collectSizeOptions(),
    addon_options: collectAddonOptions(),
  };
}

function buildBannerPayload() {
  const title = bannerFormNodes.title.value.trim();
  if (!title) {
    throw new Error("Укажите заголовок баннера.");
  }

  return {
    title,
    subtitle: bannerFormNodes.subtitle.value.trim() || null,
    description: bannerFormNodes.description.value.trim() || null,
    image_url: bannerFormNodes.imageUrl.value.trim() || null,
    sort_order: parseOptionalInteger(bannerFormNodes.sortOrder.value, "Порядок сортировки", { max: 10000 }) ?? 100,
    is_active: bannerFormNodes.isActive.checked,
  };
}

function buildBaristaPayload() {
  const fullName = baristaFormNodes.fullName.value.trim();
  if (!fullName) {
    throw new Error("Укажите имя бариста.");
  }

  return {
    username: baristaFormNodes.username.value.trim().replace(/^@+/, "") || null,
    full_name: fullName,
    is_barista: baristaFormNodes.isActive.checked,
  };
}

function buildShiftPayload() {
  const userId = parsePositiveInteger(shiftFormNodes.userId.value, "Бариста");
  const weekday = parseOptionalInteger(shiftFormNodes.weekday.value, "День недели", { max: 6 });
  const startTime = String(shiftFormNodes.startTime.value || "").trim();
  const endTime = String(shiftFormNodes.endTime.value || "").trim();
  if (!/^\d{2}:\d{2}$/.test(startTime)) {
    throw new Error('Укажите "Начало смены".');
  }
  if (!/^\d{2}:\d{2}$/.test(endTime)) {
    throw new Error('Укажите "Конец смены".');
  }
  if (endTime <= startTime) {
    throw new Error("Конец смены должен быть позже начала.");
  }

  return {
    user_id: userId,
    weekday,
    start_time: startTime,
    end_time: endTime,
    note: shiftFormNodes.note.value.trim() || null,
    is_active: shiftFormNodes.isActive.checked,
  };
}

function getLoyaltyCategoryOptionLabel(category) {
  if (!category) {
    return "";
  }
  return category.is_active ? category.name : `${category.name} (скрыта)`;
}

function renderLoyaltyCategoryOptions() {
  if (!loyaltyFormNodes.categoryOptions) {
    return;
  }

  const selectedSlugs = normalizeLoyaltyCategorySlugs(
    getCurrentLoyaltyCategorySlugs().length
      ? getCurrentLoyaltyCategorySlugs()
      : state.loyaltySettings.classic_category_slugs || state.loyaltySettings.classic_category_slug,
  );

  if (!state.categories.length) {
    loyaltyFormNodes.categoryOptions.innerHTML = '<div class="config-empty">Сначала создайте хотя бы одну категорию.</div>';
    return;
  }

  const knownSlugs = new Set(state.categories.map((category) => category.slug));
  const extraCategories = selectedSlugs
    .filter((slug) => !knownSlugs.has(slug))
    .map((slug) => ({ slug, name: slug, is_active: false }));
  const categories = [...state.categories, ...extraCategories];

  loyaltyFormNodes.categoryOptions.innerHTML = categories.map((category) => {
    const checked = selectedSlugs.includes(category.slug) ? "checked" : "";
    const hint = category.is_active ? "Участвует в общей программе лояльности." : "Категория скрыта, но правило для нее сохранено.";
    return `
      <label class="selection-option">
        <input type="checkbox" name="loyaltyCategorySlugs" value="${escapeHtml(category.slug)}" ${checked} />
        <span>
          <strong>${escapeHtml(getLoyaltyCategoryOptionLabel(category))}</strong>
          <small>${escapeHtml(hint)}</small>
        </span>
      </label>
    `;
  }).join("");
}

function getLoyaltyCategoryNames(slugs) {
  return normalizeLoyaltyCategorySlugs(slugs).map((slug) => {
    const category = state.categories.find((item) => item.slug === slug);
    return category?.name || slug;
  });
}

function renderLoyaltyPreview() {
  const selectedSlugs = normalizeLoyaltyCategorySlugs(
    getCurrentLoyaltyCategorySlugs().length
      ? getCurrentLoyaltyCategorySlugs()
      : state.loyaltySettings.classic_category_slugs || state.loyaltySettings.classic_category_slug,
  );
  const categoryNames = getLoyaltyCategoryNames(selectedSlugs);
  const paidItemsPerReward = Math.max(
    1,
    Number.parseInt(loyaltyFormNodes.paidItemsPerReward.value || state.loyaltySettings.paid_items_per_reward || 5, 10) || 5,
  );
  const bonusEnabled = loyaltyFormNodes.bonusEnabled.checked;
  const bonusEarnPercent = Math.max(
    0,
    Number.parseInt(loyaltyFormNodes.bonusEarnPercent.value || state.loyaltySettings.bonus_earn_percent || 5, 10) || 0,
  );
  const bonusRedeemEnabled = loyaltyFormNodes.bonusRedeemEnabled.checked;
  const bonusRedeemMaxPercent = Math.max(
    0,
    Number.parseInt(loyaltyFormNodes.bonusRedeemMaxPercent.value || state.loyaltySettings.bonus_redeem_max_percent || 100, 10) || 0,
  );
  const bonusStatus = bonusEnabled ? `${bonusEarnPercent}% начисления` : "начисление отключено";
  const redeemStatus = bonusRedeemEnabled ? `списание до ${bonusRedeemMaxPercent}%` : "списание отключено";
  nodes.loyaltyPreviewText.textContent = `Лояльность: каждый ${paidItemsPerReward + 1}-й товар из ${formatCategoryNamesList(categoryNames)} бесплатно. Бонусы: ${bonusStatus}, ${redeemStatus}.`;
}

function buildLoyaltyPayload() {
  const selectedCategorySlugs = getCurrentLoyaltyCategorySlugs()
    .map((value) => slugify(String(value ?? "")))
    .filter(Boolean);
  const classicCategorySlugs = normalizeLoyaltyCategorySlugs(selectedCategorySlugs);
  if (!classicCategorySlugs.length) {
    throw new Error("Выберите хотя бы одну категорию для программы лояльности.");
  }

  return {
    classic_category_slug: classicCategorySlugs[0],
    classic_category_slugs: classicCategorySlugs,
    paid_items_per_reward: parsePositiveInteger(
      loyaltyFormNodes.paidItemsPerReward.value,
      "Платных товаров до бесплатного",
      { max: 100 },
    ),
    bonus_enabled: loyaltyFormNodes.bonusEnabled.checked,
    bonus_earn_percent: Math.max(
      0,
      parseOptionalInteger(loyaltyFormNodes.bonusEarnPercent.value, "Начисление бонусов, %", { max: 100 }) ?? 0,
    ),
    bonus_redeem_enabled: loyaltyFormNodes.bonusRedeemEnabled.checked,
    bonus_redeem_max_percent: Math.max(
      0,
      parseOptionalInteger(loyaltyFormNodes.bonusRedeemMaxPercent.value, "Максимум оплаты бонусами, %", { max: 100 }) ?? 0,
    ),
  };
}

function resetBaristaForm() {
  baristaFormNodes.id.value = "";
  baristaFormNodes.fullName.value = "";
  baristaFormNodes.username.value = "";
  baristaFormNodes.isActive.checked = true;
  clearMessage(nodes.baristaMessage);
}

function resetShiftForm() {
  shiftFormNodes.id.value = "";
  shiftFormNodes.userId.value = "";
  shiftFormNodes.weekday.value = "0";
  shiftFormNodes.startTime.value = "";
  shiftFormNodes.endTime.value = "";
  shiftFormNodes.note.value = "";
  shiftFormNodes.isActive.checked = true;
  clearMessage(nodes.shiftMessage);
}

function resetCategoryForm() {
  categoryFormNodes.id.value = "";
  categoryFormNodes.name.value = "";
  categoryFormNodes.slug.value = "";
  categoryFormNodes.sortOrder.value = "100";
  categoryFormNodes.isActive.checked = true;
  categorySlugTouched = false;
  clearMessage(nodes.categoryMessage);
}

function fillLoyaltyForm(loyaltySettings = state.loyaltySettings) {
  const defaults = defaultProgramSettings();
  const classicCategorySlugs = normalizeLoyaltyCategorySlugs(
    loyaltySettings?.classic_category_slugs || loyaltySettings?.classic_category_slug || defaults.classic_category_slugs,
  );
  state.loyaltySettings = {
    classic_category_slug: classicCategorySlugs[0] || defaults.classic_category_slug,
    classic_category_slugs: classicCategorySlugs,
      paid_items_per_reward: Number(loyaltySettings?.paid_items_per_reward || defaults.paid_items_per_reward),
      bonus_enabled: loyaltySettings?.bonus_enabled ?? defaults.bonus_enabled,
      bonus_earn_percent: Number(loyaltySettings?.bonus_earn_percent ?? defaults.bonus_earn_percent),
      bonus_redeem_enabled: loyaltySettings?.bonus_redeem_enabled ?? defaults.bonus_redeem_enabled,
      bonus_redeem_max_percent: Number(loyaltySettings?.bonus_redeem_max_percent ?? defaults.bonus_redeem_max_percent),
    };
  renderLoyaltyCategoryOptions();
  loyaltyFormNodes.paidItemsPerReward.value = String(Math.max(1, state.loyaltySettings.paid_items_per_reward));
    loyaltyFormNodes.bonusEnabled.checked = Boolean(state.loyaltySettings.bonus_enabled);
    loyaltyFormNodes.bonusEarnPercent.value = String(Math.max(0, state.loyaltySettings.bonus_earn_percent));
    loyaltyFormNodes.bonusRedeemEnabled.checked = Boolean(state.loyaltySettings.bonus_redeem_enabled);
    loyaltyFormNodes.bonusRedeemMaxPercent.value = String(Math.max(0, state.loyaltySettings.bonus_redeem_max_percent));
    clearMessage(nodes.loyaltyMessage);
    renderLoyaltyPreview();
}

function resetLoyaltyForm() {
  fillLoyaltyForm(state.loyaltySettings);
}

function resetProductForm() {
  productFormNodes.id.value = "";
  productFormNodes.categoryId.value = "";
  productFormNodes.productType.value = "";
  productFormNodes.name.value = "";
  productFormNodes.badge.value = "";
  productFormNodes.description.value = "";
  productFormNodes.composition.value = "";
  productFormNodes.caloriesKcal.value = "";
  productFormNodes.sortOrder.value = "100";
  productFormNodes.isActive.checked = true;
  renderSizeOptionRows([{}]);
  renderAddonOptionRows([]);
  applyUploadState({
    url: "",
    hiddenInput: productFormNodes.imageUrl,
    pathNode: nodes.productImagePath,
    previewNode: nodes.productImagePreview,
    fileNode: nodes.productImageFile,
  });
  clearMessage(nodes.productMessage);
}

function resetBannerForm() {
  bannerFormNodes.id.value = "";
  bannerFormNodes.title.value = "";
  bannerFormNodes.subtitle.value = "";
  bannerFormNodes.description.value = "";
  bannerFormNodes.sortOrder.value = "100";
  bannerFormNodes.isActive.checked = true;
  applyUploadState({
    url: "",
    hiddenInput: bannerFormNodes.imageUrl,
    pathNode: nodes.bannerImagePath,
    previewNode: nodes.bannerImagePreview,
    fileNode: nodes.bannerImageFile,
  });
  clearMessage(nodes.bannerMessage);
}

function fillCategoryForm(category) {
  categoryFormNodes.id.value = String(category.id);
  categoryFormNodes.name.value = category.name;
  categoryFormNodes.slug.value = category.slug;
  categoryFormNodes.sortOrder.value = String(category.sort_order);
  categoryFormNodes.isActive.checked = category.is_active;
  categorySlugTouched = true;
  clearMessage(nodes.categoryMessage);
  categoryFormNodes.name.focus();
}

function fillProductForm(product) {
  productFormNodes.id.value = String(product.id);
  productFormNodes.categoryId.value = product.category_id ? String(product.category_id) : "";
  productFormNodes.productType.value = product.product_type || "";
  productFormNodes.name.value = product.name || "";
  productFormNodes.badge.value = product.badge || "";
  productFormNodes.description.value = product.description || "";
  productFormNodes.composition.value = product.composition || "";
  productFormNodes.caloriesKcal.value = product.calories_kcal ?? "";
  productFormNodes.sortOrder.value = String(product.sort_order ?? 100);
  productFormNodes.isActive.checked = Boolean(product.is_active);
  renderSizeOptionRows(product.size_options?.length ? product.size_options : [{}]);
  renderAddonOptionRows(product.addon_options || []);
  applyUploadState({
    url: product.image_url || "",
    hiddenInput: productFormNodes.imageUrl,
    pathNode: nodes.productImagePath,
    previewNode: nodes.productImagePreview,
    fileNode: nodes.productImageFile,
  });
  clearMessage(nodes.productMessage);
  productFormNodes.name.focus();
}

function fillBannerForm(banner) {
  bannerFormNodes.id.value = String(banner.id);
  bannerFormNodes.title.value = banner.title || "";
  bannerFormNodes.subtitle.value = banner.subtitle || "";
  bannerFormNodes.description.value = banner.description || "";
  bannerFormNodes.sortOrder.value = String(banner.sort_order ?? 100);
  bannerFormNodes.isActive.checked = Boolean(banner.is_active);
  applyUploadState({
    url: banner.image_url || "",
    hiddenInput: bannerFormNodes.imageUrl,
    pathNode: nodes.bannerImagePath,
    previewNode: nodes.bannerImagePreview,
    fileNode: nodes.bannerImageFile,
  });
  clearMessage(nodes.bannerMessage);
  bannerFormNodes.title.focus();
}

function fillBaristaForm(barista) {
  baristaFormNodes.id.value = String(barista.id);
  baristaFormNodes.fullName.value = barista.full_name || "";
  baristaFormNodes.username.value = barista.username || "";
  baristaFormNodes.isActive.checked = Boolean(barista.is_barista);
  clearMessage(nodes.baristaMessage);
  baristaFormNodes.fullName.focus();
}

function fillShiftForm(shift) {
  shiftFormNodes.id.value = String(shift.id);
  shiftFormNodes.userId.value = String(shift.user_id || "");
  shiftFormNodes.weekday.value = String(shift.weekday ?? 0);
  shiftFormNodes.startTime.value = String(shift.start_time || "").slice(0, 5);
  shiftFormNodes.endTime.value = String(shift.end_time || "").slice(0, 5);
  shiftFormNodes.note.value = shift.note || "";
  shiftFormNodes.isActive.checked = Boolean(shift.is_active);
  clearMessage(nodes.shiftMessage);
  shiftFormNodes.userId.focus();
}

function renderCategorySelects() {
  const currentProductCategoryValue = productFormNodes.categoryId.value;
  const filterExists = state.filterCategory === "all"
    || state.filterCategory === "uncategorized"
    || state.categories.some((category) => String(category.id) === String(state.filterCategory));
  if (!filterExists) {
    state.filterCategory = "all";
  }

  const options = [
    '<option value="">Без категории</option>',
    ...state.categories.map(
      (category) => `<option value="${category.id}">${escapeHtml(category.name)}${category.is_active ? "" : " (скрыта)"}</option>`,
    ),
  ];
  productFormNodes.categoryId.innerHTML = options.join("");
  productFormNodes.categoryId.value = state.categories.some(
    (category) => String(category.id) === String(currentProductCategoryValue),
  )
    ? String(currentProductCategoryValue)
    : "";

  const filterOptions = [
    '<option value="all">Все категории</option>',
    '<option value="uncategorized">Без категории</option>',
    ...state.categories.map((category) => `<option value="${category.id}">${escapeHtml(category.name)}</option>`),
  ];
  nodes.productFilterCategory.innerHTML = filterOptions.join("");
  nodes.productFilterCategory.value = state.filterCategory;
}

function renderBaristaSelects() {
  const currentShiftBaristaValue = shiftFormNodes.userId.value;
  const baristaOptions = [
    '<option value="">Выберите бариста</option>',
    ...state.baristas.map(
      (barista) => `<option value="${barista.id}">${escapeHtml(getBaristaDisplayName(barista))}${barista.is_barista ? "" : " (отключен)"}</option>`,
    ),
  ];
  shiftFormNodes.userId.innerHTML = baristaOptions.join("");
  shiftFormNodes.userId.value = state.baristas.some((barista) => String(barista.id) === String(currentShiftBaristaValue))
    ? String(currentShiftBaristaValue)
    : "";
}

function getBaristaShiftSummary(baristaId) {
  const now = new Date();
  const currentWeekday = now.getDay() === 0 ? 6 : now.getDay() - 1;
  const currentTime = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  const activeShift = state.baristaShifts.find((shift) => (
    Number(shift.user_id) === Number(baristaId)
      && shift.is_active
      && Number(shift.weekday) === currentWeekday
      && String(shift.start_time || "") <= currentTime
      && String(shift.end_time || "") > currentTime
  ));
  if (activeShift) {
    return {
      text: `Сейчас в смене до ${String(activeShift.end_time || "").slice(0, 5)}`,
      kind: "active-pill",
    };
  }

  const nextShift = state.baristaShifts
    .filter((shift) => Number(shift.user_id) === Number(baristaId) && shift.is_active)
    .sort((left, right) => {
      if (Number(left.weekday) !== Number(right.weekday)) {
        return Number(left.weekday) - Number(right.weekday);
      }
      return String(left.start_time || "").localeCompare(String(right.start_time || ""));
    })[0];
  if (nextShift) {
    return {
      text: `По расписанию: ${WEEKDAY_LABELS[Number(nextShift.weekday) || 0]} ${String(nextShift.start_time || "").slice(0, 5)}-${String(nextShift.end_time || "").slice(0, 5)}`,
      kind: "",
    };
  }

  return {
    text: "Смен пока нет",
    kind: "inactive-pill",
  };
}

function renderBaristas() {
  if (!state.baristas.length) {
    nodes.baristaList.innerHTML = '<div class="entity-card"><p>Баристы пока не добавлены. Создайте первую запись для команды.</p></div>';
    return;
  }

  nodes.baristaList.innerHTML = state.baristas
    .map((barista) => {
      const isSelected = Number(baristaFormNodes.id.value || 0) === barista.id;
      const shiftsCount = state.baristaShifts.filter((shift) => Number(shift.user_id) === Number(barista.id)).length;
      const shiftSummary = getBaristaShiftSummary(barista.id);
      return `
        <article class="entity-card ${isSelected ? "active" : ""}">
          <h4>${escapeHtml(getBaristaDisplayName(barista))}</h4>
          <div class="entity-meta">
            <span class="meta-pill ${barista.is_pending ? "inactive-pill" : ""}">${escapeHtml(getBaristaBindingLabel(barista))}</span>
            ${barista.username ? `<span class="meta-pill">@${escapeHtml(barista.username)}</span>` : ""}
            <span class="meta-pill">Смен: ${shiftsCount}</span>
            <span class="meta-pill ${barista.is_barista ? "active-pill" : "inactive-pill"}">
              ${barista.is_barista ? "Активен" : "Отключен"}
            </span>
          </div>
          <p class="entity-copy">
            <span class="meta-pill ${shiftSummary.kind}">${escapeHtml(shiftSummary.text)}</span>
          </p>
          <button class="secondary-button" type="button" data-edit-barista="${barista.id}">Редактировать</button>
        </article>
      `;
    })
    .join("");
}

function getShiftStatusMeta(shift) {
  const now = new Date();
  const currentWeekday = now.getDay() === 0 ? 6 : now.getDay() - 1;
  const currentTime = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  if (!shift.is_active) {
    return { label: "Выключена", className: "inactive-pill" };
  }
  if (
    Number(shift.weekday) === currentWeekday
    && String(shift.start_time || "") <= currentTime
    && String(shift.end_time || "") > currentTime
  ) {
    return { label: "Идет сейчас", className: "active-pill" };
  }
  return { label: "По расписанию", className: "" };
}

function renderShifts() {
  if (!state.baristaShifts.length) {
    nodes.shiftList.innerHTML = '<div class="entity-card"><p>Окон расписания пока нет. Добавьте первое окно для баристы.</p></div>';
    return;
  }

  const sortedShifts = [...state.baristaShifts].sort((left, right) => {
    if (Number(left.weekday) !== Number(right.weekday)) {
      return Number(left.weekday) - Number(right.weekday);
    }
    return String(left.start_time || "").localeCompare(String(right.start_time || ""));
  });
  nodes.shiftList.innerHTML = sortedShifts
    .map((shift) => {
      const isSelected = Number(shiftFormNodes.id.value || 0) === shift.id;
      const statusMeta = getShiftStatusMeta(shift);
      return `
        <article class="entity-card ${isSelected ? "active" : ""}">
          <h4>${escapeHtml(shift.barista_name)}</h4>
          <div class="entity-meta">
            <span class="meta-pill ${statusMeta.className}">${escapeHtml(statusMeta.label)}</span>
            ${shift.barista_username ? `<span class="meta-pill">@${escapeHtml(shift.barista_username)}</span>` : ""}
            ${shift.barista_is_pending ? '<span class="meta-pill inactive-pill">Ждет привязку</span>' : ""}
          </div>
          <p class="entity-copy">${escapeHtml(`${WEEKDAY_LABELS[Number(shift.weekday) || 0]} ${String(shift.start_time || "").slice(0, 5)} - ${String(shift.end_time || "").slice(0, 5)}`)}</p>
          ${shift.note ? `<p>${escapeHtml(shift.note)}</p>` : ""}
          <div class="inline-actions">
            <button class="secondary-button" type="button" data-edit-shift="${shift.id}">Редактировать</button>
            <button class="ghost-button danger-button" type="button" data-delete-shift="${shift.id}">Удалить</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderCategories() {
  if (!state.categories.length) {
    nodes.categoryList.innerHTML = '<div class="entity-card"><p>Категорий пока нет. Создайте первую категорию.</p></div>';
    return;
  }

  const countsByCategory = new Map();
  for (const product of state.products) {
    if (product.category_id) {
      countsByCategory.set(product.category_id, (countsByCategory.get(product.category_id) || 0) + 1);
    }
  }

  nodes.categoryList.innerHTML = state.categories
    .map((category) => {
      const isSelected = Number(categoryFormNodes.id.value || 0) === category.id;
      return `
        <article class="entity-card ${isSelected ? "active" : ""}">
          <h4>${escapeHtml(category.name)}</h4>
          <div class="entity-meta">
            <span class="meta-pill">${escapeHtml(category.slug)}</span>
            <span class="meta-pill">Товаров: ${countsByCategory.get(category.id) || 0}</span>
            <span class="meta-pill ${category.is_active ? "active-pill" : "inactive-pill"}">
              ${category.is_active ? "Активна" : "Скрыта"}
            </span>
          </div>
          <button class="secondary-button" type="button" data-edit-category="${category.id}">Редактировать</button>
        </article>
      `;
    })
    .join("");
}

function getFilteredProducts() {
  if (state.filterCategory === "all") {
    return state.products;
  }
  if (state.filterCategory === "uncategorized") {
    return state.products.filter((product) => !product.category_id);
  }
  return state.products.filter((product) => String(product.category_id) === String(state.filterCategory));
}

function renderProducts() {
  const products = getFilteredProducts();
  if (!products.length) {
    nodes.productList.innerHTML = '<div class="product-card"><p>По текущему фильтру товаров нет.</p></div>';
    return;
  }

  nodes.productList.innerHTML = products
    .map((product) => {
      const isSelected = Number(productFormNodes.id.value || 0) === product.id;
      const specs = [
        product.product_type,
        product.calories_kcal ? `${product.calories_kcal} ккал` : null,
      ].filter(Boolean);

      return `
        <article class="product-card ${isSelected ? "active" : ""}">
          <div class="price-mark">${product.size_options?.length > 1 ? `от ${formatMoney(product.price_cents)}` : formatMoney(product.price_cents)}</div>
          <h4>${escapeHtml(product.name)}</h4>
          <p>${escapeHtml(product.category_name || "Без категории")}</p>
          <div class="product-meta">
            ${product.badge ? `<span class="meta-pill">${escapeHtml(product.badge)}</span>` : ""}
            <span class="meta-pill ${product.is_active ? "active-pill" : "inactive-pill"}">
              ${product.is_active ? "Активен" : "Скрыт"}
            </span>
            ${product.size_options?.length ? `<span class="meta-pill">Размеров: ${product.size_options.length}</span>` : ""}
            ${product.addon_options?.length ? `<span class="meta-pill">Допов: ${product.addon_options.length}</span>` : ""}
          </div>
          ${specs.length ? `<div class="spec-list">${specs.map((item) => `<span class="meta-pill">${escapeHtml(item)}</span>`).join("")}</div>` : ""}
          <button class="secondary-button" type="button" data-edit-product="${product.id}">Редактировать</button>
        </article>
      `;
    })
    .join("");
}

function hideLegacyProductFields() {
  document.getElementById("productSku")?.closest(".field")?.remove();
  document.getElementById("productCaffeineMg")?.closest(".field")?.remove();
  document.getElementById("bannerCtaLabel")?.closest(".field")?.remove();
  document.getElementById("analyticsHourlyBreakdown")?.closest(".content-card")?.remove();
  const shiftWeekdayLabel = document.getElementById("shiftWeekday")?.closest(".field")?.querySelector("span");
  if (shiftWeekdayLabel) {
    shiftWeekdayLabel.textContent = "День недели";
  }
  const shiftStartLabel = document.getElementById("shiftStartTime")?.closest(".field")?.querySelector("span");
  if (shiftStartLabel) {
    shiftStartLabel.textContent = "Начало смены";
  }
  const shiftEndLabel = document.getElementById("shiftEndTime")?.closest(".field")?.querySelector("span");
  if (shiftEndLabel) {
    shiftEndLabel.textContent = "Конец смены";
  }
}
function renderBanners() {
  if (!state.banners.length) {
    nodes.bannerList.innerHTML = '<div class="banner-admin-card"><p>Баннеров пока нет. Создайте первый баннер для главной страницы.</p></div>';
    return;
  }

  nodes.bannerList.innerHTML = state.banners
    .map((banner) => {
      const isSelected = Number(bannerFormNodes.id.value || 0) === banner.id;
      return `
        <article class="banner-admin-card ${isSelected ? "active" : ""}">
          ${banner.image_url ? `<img src="${escapeHtml(banner.image_url)}" alt="${escapeHtml(banner.title)}" class="banner-admin-image" />` : '<div class="banner-admin-image banner-admin-image-empty">Без изображения</div>'}
          <div class="banner-admin-content">
            <div class="banner-admin-head">
              <div>
                <h4>${escapeHtml(banner.title)}</h4>
                ${banner.subtitle ? `<p>${escapeHtml(banner.subtitle)}</p>` : ""}
              </div>
              <span class="meta-pill ${banner.is_active ? "active-pill" : "inactive-pill"}">
                ${banner.is_active ? "Активен" : "Скрыт"}
              </span>
            </div>
            <div class="entity-meta">
              <span class="meta-pill">Порядок: ${banner.sort_order}</span>
            </div>
            ${banner.description ? `<p>${escapeHtml(banner.description)}</p>` : ""}
            <button class="secondary-button" type="button" data-edit-banner="${banner.id}">Редактировать</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderSummary() {
  nodes.categoryCount.textContent = String(state.categories.length);
  nodes.productCount.textContent = String(state.products.length);
  nodes.bannerCount.textContent = String(state.banners.length);
  nodes.activeProductCount.textContent = String(state.products.filter((item) => item.is_active).length);
}

function buildAnalyticsEntityList(items, renderItem) {
  if (!Array.isArray(items) || !items.length) {
    return '<article class="entity-card"><div><h4>Пока нет данных</h4><p>За выбранный период статистика еще не накопилась.</p></div></article>';
  }
  return items.map(renderItem).join("");
}

function renderAnalytics() {
  const analytics = state.analytics;
  if (!analytics) {
    nodes.analyticsKpis.innerHTML = "";
    nodes.analyticsTopProducts.innerHTML = "";
    nodes.analyticsTopCategories.innerHTML = "";
    nodes.analyticsPromoUsage.innerHTML = "";
    nodes.analyticsStatusBreakdown.innerHTML = "";
    nodes.analyticsDailyRevenue.innerHTML = "";
    return;
  }

  const kpis = analytics.kpis || {};
  const kpiItems = [
    ["Всего заказов", kpis.total_orders ?? 0],
    ["Завершено", kpis.completed_orders ?? 0],
    ["Отменено", kpis.cancelled_orders ?? 0],
    ["Конверсия", `${Number(kpis.completion_rate ?? 0).toFixed(2)}%`],
    ["Валовая сумма", formatMoney(kpis.gross_revenue_cents ?? 0)],
    ["Выручка", formatMoney(kpis.net_revenue_cents ?? 0)],
    ["Средний чек", formatMoney(kpis.average_order_value_cents ?? 0)],
    ["Уникальные клиенты", kpis.unique_customers ?? 0],
    ["Повторные клиенты", kpis.repeat_customers ?? 0],
    ["Списано бонусов", formatMoney(kpis.bonus_spent_cents ?? 0)],
    ["Начислено бонусов", formatMoney(kpis.bonus_earned_cents ?? 0)],
    ["Скидка по промо", formatMoney(kpis.promo_discount_cents ?? 0)],
    ["Скидка по лояльности", formatMoney(kpis.loyalty_discount_cents ?? 0)],
  ];
  nodes.analyticsKpis.innerHTML = kpiItems
    .map(([label, value]) => `
      <article class="summary-card">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
      </article>
    `)
    .join("");

  nodes.analyticsTopProducts.innerHTML = buildAnalyticsEntityList(analytics.top_products, (item) => `
    <article class="entity-card">
      <div>
        <h4>${escapeHtml(item.name)}</h4>
        <p>Количество: ${escapeHtml(item.qty)} · Выручка: ${escapeHtml(formatMoney(item.revenue_cents))}</p>
      </div>
    </article>
  `);
  nodes.analyticsTopCategories.innerHTML = buildAnalyticsEntityList(analytics.top_categories, (item) => `
    <article class="entity-card">
      <div>
        <h4>${escapeHtml(item.name)}</h4>
        <p>Количество: ${escapeHtml(item.qty)} · Выручка: ${escapeHtml(formatMoney(item.revenue_cents))}</p>
      </div>
    </article>
  `);
  nodes.analyticsPromoUsage.innerHTML = buildAnalyticsEntityList(analytics.promo_usage, (item) => `
    <article class="entity-card">
      <div>
        <h4>${escapeHtml(item.code)}</h4>
        <p>Использований: ${escapeHtml(item.uses)} · Скидка: ${escapeHtml(formatMoney(item.discount_cents))}</p>
      </div>
    </article>
  `);
  nodes.analyticsStatusBreakdown.innerHTML = buildAnalyticsEntityList(analytics.status_breakdown, (item) => `
    <article class="entity-card">
      <div>
        <h4>${escapeHtml(item.status)}</h4>
        <p>Заказов: ${escapeHtml(item.qty)}</p>
      </div>
    </article>
  `);
  nodes.analyticsDailyRevenue.innerHTML = buildAnalyticsEntityList(analytics.daily_revenue, (item) => `
    <article class="entity-card">
      <div>
        <h4>${escapeHtml(formatDate(item.day))}</h4>
        <p>Заказов: ${escapeHtml(item.orders)} · Выручка: ${escapeHtml(formatMoney(item.revenue_cents))}</p>
      </div>
    </article>
  `);
}

function renderDashboard() {
  renderSummary();
  fillLoyaltyForm(state.loyaltySettings);
  fillAppSettingsForm(state.appSettings);
  fillReminderForm(state.reminderSettings);
  renderCategorySelects();
  renderBaristaSelects();
  renderBaristas();
  renderShifts();
  renderCategories();
  renderProducts();
  renderBanners();
  renderAnalytics();
  switchAdminTab(state.activeTab);
}

async function loadDashboard() {
  clearMessage(nodes.authMessage);
  clearMessage(nodes.dashboardMessage);

  try {
    const data = await apiRequest("/api/admin/bootstrap");
    state.banners = Array.isArray(data.banners) ? data.banners : [];
    state.baristas = Array.isArray(data.baristas) ? data.baristas : [];
    state.baristaShifts = Array.isArray(data.barista_shifts) ? data.barista_shifts : [];
    state.categories = Array.isArray(data.categories) ? data.categories : [];
    state.loyaltySettings = data.program_settings || data.loyalty_settings || defaultProgramSettings();
    state.appSettings = {
      ...defaultAppSettings(),
      ...(data.app_settings || {}),
    };
    state.reminderSettings = {
      ...defaultReminderSettings(),
      ...(data.reminder_settings || {}),
    };
    state.analytics = null;
    state.products = Array.isArray(data.products) ? data.products : [];
    setAuthenticated(true);
    renderDashboard();
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession(nodes.dashboard.classList.contains("hidden") ? "" : "Сессия истекла. Войдите снова.");
      return;
    }
    const messageNode = nodes.dashboard.classList.contains("hidden")
      ? nodes.authMessage
      : nodes.dashboardMessage;
    showMessage(messageNode, error.message, "error");
  }
}

async function handleLogin(event) {
  event.preventDefault();
  clearMessage(nodes.authMessage);
  if (!ensureFormValidity(nodes.loginForm, nodes.authMessage)) {
    return;
  }

  const secretValue = nodes.secretInput.value.trim();
  if (!secretValue) {
    showMessage(nodes.authMessage, "Введите секрет бариста.", "error");
    nodes.secretInput.focus();
    return;
  }
  try {
    await apiRequest("/api/admin/login", {
      method: "POST",
      body: { secret: secretValue },
    });
    nodes.secretInput.value = "";
    await loadDashboard();
  } catch (error) {
    showMessage(nodes.authMessage, error.message, "error");
  }
}

async function handleLogout() {
  try {
    await apiRequest("/api/admin/logout", { method: "POST" });
  } finally {
    state.banners = [];
    state.baristas = [];
    state.baristaShifts = [];
    state.categories = [];
    state.loyaltySettings = defaultProgramSettings();
    state.appSettings = defaultAppSettings();
    state.reminderSettings = defaultReminderSettings();
    state.analytics = null;
    state.products = [];
    state.activeTab = "programs";
    state.activeSubtabs = { ...DEFAULT_ADMIN_SUBTABS };
    setAuthenticated(false);
    resetLoyaltyForm();
    resetAppSettingsForm();
    resetBaristaForm();
    resetShiftForm();
    resetCategoryForm();
    resetProductForm();
    resetBannerForm();
    clearMessage(nodes.dashboardMessage);
  }
}

async function handleLoyaltySubmit(event) {
  event.preventDefault();
  clearMessage(nodes.loyaltyMessage);
  if (!ensureFormValidity(nodes.loyaltyForm, nodes.loyaltyMessage)) {
    return;
  }

  try {
    const saved = await apiRequest("/api/admin/program-settings", {
      method: "PUT",
      body: buildLoyaltyPayload(),
    });
    state.loyaltySettings = saved;
    await loadDashboard();
    fillLoyaltyForm(saved);
    showMessage(nodes.loyaltyMessage, "Настройки лояльности и бонусов сохранены.", "success");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.loyaltyMessage, error.message, "error");
  }
}

async function handleAppSettingsSubmit(event) {
  event.preventDefault();
  clearMessage(nodes.appSettingsMessage);
  if (!ensureFormValidity(nodes.appSettingsForm, nodes.appSettingsMessage)) {
    return;
  }

  try {
    const saved = await apiRequest("/api/admin/app-settings", {
      method: "PUT",
      body: buildAppSettingsPayload(),
    });
    state.appSettings = {
      ...defaultAppSettings(),
      ...(saved || {}),
    };
    fillAppSettingsForm(state.appSettings);
    showMessage(nodes.appSettingsMessage, "Тексты бота сохранены.", "success");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.appSettingsMessage, error.message, "error");
  }
}

function getAnalyticsQueryString() {
  const params = new URLSearchParams();
  if (nodes.analyticsDateFrom?.value) {
    params.set("date_from", nodes.analyticsDateFrom.value);
  }
  if (nodes.analyticsDateTo?.value) {
    params.set("date_to", nodes.analyticsDateTo.value);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

async function loadAnalytics() {
  clearMessage(nodes.analyticsMessage);
  try {
    state.analytics = await apiRequest(`/api/admin/analytics${getAnalyticsQueryString()}`);
    renderAnalytics();
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.analyticsMessage, error.message, "error");
  }
}

async function handleReminderSubmit(event) {
  event.preventDefault();
  clearMessage(nodes.reminderMessage);
  if (!ensureFormValidity(nodes.reminderForm, nodes.reminderMessage)) {
    return;
  }
  try {
    const saved = await apiRequest("/api/admin/reminders/settings", {
      method: "PUT",
      body: buildReminderPayload(),
    });
    state.reminderSettings = {
      ...defaultReminderSettings(),
      ...(saved || {}),
    };
    fillReminderForm(state.reminderSettings);
    showMessage(nodes.reminderMessage, "Напоминалки сохранены.", "success");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.reminderMessage, error.message, "error");
  }
}

function setAnalyticsPreset(days) {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - (days - 1));
  if (nodes.analyticsDateFrom) {
    nodes.analyticsDateFrom.value = formatDate(start);
  }
  if (nodes.analyticsDateTo) {
    nodes.analyticsDateTo.value = formatDate(end);
  }
}

function downloadWithSession(url, filename) {
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

async function handleBaristaSubmit(event) {
  event.preventDefault();
  clearMessage(nodes.baristaMessage);
  if (!ensureFormValidity(nodes.baristaForm, nodes.baristaMessage)) {
    return;
  }

  try {
    const payload = buildBaristaPayload();
    const baristaId = baristaFormNodes.id.value;
    const saved = await apiRequest(
      baristaId ? `/api/admin/baristas/${baristaId}` : "/api/admin/baristas",
      {
        method: baristaId ? "PUT" : "POST",
        body: payload,
      },
    );
    await loadDashboard();
    switchAdminTab("team", "baristas");
    fillBaristaForm(saved);
    renderBaristas();
    renderBaristaSelects();
    showMessage(nodes.baristaMessage, "Карточка бариста сохранена.", "success");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.baristaMessage, error.message, "error");
  }
}

async function handleShiftSubmit(event) {
  event.preventDefault();
  clearMessage(nodes.shiftMessage);
  if (!ensureFormValidity(nodes.shiftForm, nodes.shiftMessage)) {
    return;
  }

  try {
    const payload = buildShiftPayload();
    const shiftId = shiftFormNodes.id.value;
    const saved = await apiRequest(
      shiftId ? `/api/admin/barista-shifts/${shiftId}` : "/api/admin/barista-shifts",
      {
        method: shiftId ? "PUT" : "POST",
        body: payload,
      },
    );
    await loadDashboard();
    switchAdminTab("team", "shifts");
    fillShiftForm(saved);
    renderShifts();
    showMessage(nodes.shiftMessage, "Смена сохранена.", "success");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.shiftMessage, error.message, "error");
  }
}

async function handleCategorySubmit(event) {
  event.preventDefault();
  clearMessage(nodes.categoryMessage);
  if (!ensureFormValidity(nodes.categoryForm, nodes.categoryMessage)) {
    return;
  }

  try {
    const payload = buildCategoryPayload();
    const categoryId = categoryFormNodes.id.value;
    const saved = await apiRequest(
      categoryId ? `/api/admin/categories/${categoryId}` : "/api/admin/categories",
      {
        method: categoryId ? "PUT" : "POST",
        body: payload,
      },
    );
    await loadDashboard();
    fillCategoryForm(saved);
    renderCategories();
    showMessage(nodes.categoryMessage, "Категория сохранена.", "success");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.categoryMessage, error.message, "error");
  }
}

async function handleProductSubmit(event) {
  event.preventDefault();
  clearMessage(nodes.productMessage);
  if (!ensureFormValidity(nodes.productForm, nodes.productMessage)) {
    return;
  }

  try {
    const payload = buildProductPayload();
    const productId = productFormNodes.id.value;
    const saved = await apiRequest(
      productId ? `/api/admin/products/${productId}` : "/api/admin/products",
      {
        method: productId ? "PUT" : "POST",
        body: payload,
      },
    );
    await loadDashboard();
    fillProductForm(saved);
    renderProducts();
    showMessage(nodes.productMessage, "Товар сохранен.", "success");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.productMessage, error.message, "error");
  }
}

async function handleBannerSubmit(event) {
  event.preventDefault();
  clearMessage(nodes.bannerMessage);
  if (!ensureFormValidity(nodes.bannerForm, nodes.bannerMessage)) {
    return;
  }

  try {
    const payload = buildBannerPayload();
    const bannerId = bannerFormNodes.id.value;
    const saved = await apiRequest(
      bannerId ? `/api/admin/banners/${bannerId}` : "/api/admin/banners",
      {
        method: bannerId ? "PUT" : "POST",
        body: payload,
      },
    );
    await loadDashboard();
    fillBannerForm(saved);
    renderBanners();
    showMessage(nodes.bannerMessage, "Баннер сохранен.", "success");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.bannerMessage, error.message, "error");
  }
}

function handleCategoryListClick(event) {
  const button = event.target.closest("[data-edit-category]");
  if (!button) {
    return;
  }
  const category = state.categories.find((item) => item.id === Number(button.dataset.editCategory));
  if (!category) {
    return;
  }
  switchAdminTab("catalog", "categories");
  fillCategoryForm(category);
  renderCategories();
}

function handleBaristaListClick(event) {
  const button = event.target.closest("[data-edit-barista]");
  if (!button) {
    return;
  }
  const barista = state.baristas.find((item) => item.id === Number(button.dataset.editBarista));
  if (!barista) {
    return;
  }
  switchAdminTab("team", "baristas");
  fillBaristaForm(barista);
  renderBaristas();
}

async function handleShiftListClick(event) {
  const editButton = event.target.closest("[data-edit-shift]");
  if (editButton) {
    const shift = state.baristaShifts.find((item) => item.id === Number(editButton.dataset.editShift));
    if (!shift) {
      return;
    }
    switchAdminTab("team", "shifts");
    fillShiftForm(shift);
    renderShifts();
    return;
  }

  const deleteButton = event.target.closest("[data-delete-shift]");
  if (!deleteButton) {
    return;
  }

  const shift = state.baristaShifts.find((item) => item.id === Number(deleteButton.dataset.deleteShift));
  if (!shift) {
    return;
  }
  const confirmed = window.confirm(
    `Удалить окно "${shift.barista_name}" (${WEEKDAY_LABELS[Number(shift.weekday) || 0]} ${String(shift.start_time || "").slice(0, 5)}-${String(shift.end_time || "").slice(0, 5)})?`,
  );
  if (!confirmed) {
    return;
  }

  clearMessage(nodes.shiftMessage);
  try {
    await apiRequest(`/api/admin/barista-shifts/${shift.id}`, { method: "DELETE" });
    if (String(shiftFormNodes.id.value) === String(shift.id)) {
      resetShiftForm();
    }
    await loadDashboard();
    switchAdminTab("team", "shifts");
    showMessage(nodes.shiftMessage, "Окно расписания удалено.", "success");
  } catch (error) {
    if (error.status === 401) {
      handleExpiredAdminSession();
      return;
    }
    showMessage(nodes.shiftMessage, error.message, "error");
  }
}

function handleProductListClick(event) {
  const button = event.target.closest("[data-edit-product]");
  if (!button) {
    return;
  }
  const product = state.products.find((item) => item.id === Number(button.dataset.editProduct));
  if (!product) {
    return;
  }
  switchAdminTab("catalog", "products");
  fillProductForm(product);
  renderProducts();
}

function handleBannerListClick(event) {
  const button = event.target.closest("[data-edit-banner]");
  if (!button) {
    return;
  }
  const banner = state.banners.find((item) => item.id === Number(button.dataset.editBanner));
  if (!banner) {
    return;
  }
  switchAdminTab("storefront", "banners");
  fillBannerForm(banner);
  renderBanners();
}

function handleOptionRemove(event) {
  const button = event.target.closest("[data-remove-option]");
  if (!button) {
    return;
  }
  const row = button.closest(".config-row");
  if (!row) {
    return;
  }
  const kind = button.dataset.removeOption;
  row.remove();
  if (kind === "size" && !nodes.productSizeOptions.querySelector(".config-row")) {
    renderSizeOptionRows([{}]);
  }
  if (kind === "addon" && !nodes.productAddonOptions.querySelector(".config-row")) {
    renderAddonOptionRows([]);
  }
}

function init() {
  hideLegacyProductFields();
  nodes.loginForm.addEventListener("submit", handleLogin);
  nodes.logoutButton.addEventListener("click", handleLogout);
  nodes.loyaltyForm.addEventListener("submit", handleLoyaltySubmit);
  nodes.appSettingsForm.addEventListener("submit", handleAppSettingsSubmit);
  nodes.reminderForm?.addEventListener("submit", handleReminderSubmit);
  nodes.baristaForm.addEventListener("submit", handleBaristaSubmit);
  nodes.shiftForm.addEventListener("submit", handleShiftSubmit);
  nodes.adminTabs.forEach((button) => {
    button.addEventListener("click", () => switchAdminTab(button.dataset.adminTab));
  });
  nodes.adminSubtabs.forEach((button) => {
    button.addEventListener("click", () => switchAdminTab(button.dataset.adminSubtabGroup, button.dataset.adminSubtab));
  });
  nodes.categoryForm.addEventListener("submit", handleCategorySubmit);
  nodes.productForm.addEventListener("submit", handleProductSubmit);
  nodes.bannerForm.addEventListener("submit", handleBannerSubmit);
  nodes.baristaList.addEventListener("click", handleBaristaListClick);
  nodes.shiftList.addEventListener("click", handleShiftListClick);
  nodes.categoryList.addEventListener("click", handleCategoryListClick);
  nodes.productList.addEventListener("click", handleProductListClick);
  nodes.bannerList.addEventListener("click", handleBannerListClick);
  nodes.productSizeOptions.addEventListener("click", handleOptionRemove);
  nodes.productAddonOptions.addEventListener("click", handleOptionRemove);
  nodes.resetLoyaltyButton.addEventListener("click", resetLoyaltyForm);
  nodes.resetAppSettingsButton.addEventListener("click", resetAppSettingsForm);
  bindMessageReset(nodes.baristaForm, nodes.baristaMessage);
  bindMessageReset(nodes.shiftForm, nodes.shiftMessage);
  bindMessageReset(nodes.loginForm, nodes.authMessage);
  bindMessageReset(nodes.loyaltyForm, nodes.loyaltyMessage);
  bindMessageReset(nodes.appSettingsForm, nodes.appSettingsMessage);
  bindMessageReset(nodes.reminderForm, nodes.reminderMessage);
  bindMessageReset(nodes.categoryForm, nodes.categoryMessage);
  bindMessageReset(nodes.productForm, nodes.productMessage);
  bindMessageReset(nodes.bannerForm, nodes.bannerMessage);
  nodes.newBaristaButton.addEventListener("click", () => {
    switchAdminTab("team", "baristas");
    resetBaristaForm();
    renderBaristas();
  });
  nodes.newShiftButton.addEventListener("click", () => {
    switchAdminTab("team", "shifts");
    resetShiftForm();
    renderShifts();
  });
  nodes.newCategoryButton.addEventListener("click", () => {
    switchAdminTab("catalog", "categories");
    resetCategoryForm();
    renderCategories();
  });
  nodes.newProductButton.addEventListener("click", () => {
    switchAdminTab("catalog", "products");
    resetProductForm();
    renderProducts();
  });
  nodes.newBannerButton.addEventListener("click", () => {
    switchAdminTab("storefront", "banners");
    resetBannerForm();
    renderBanners();
  });
  nodes.resetBaristaButton.addEventListener("click", () => {
    resetBaristaForm();
    renderBaristas();
  });
  nodes.resetShiftButton.addEventListener("click", () => {
    resetShiftForm();
    renderShifts();
  });
  nodes.resetCategoryButton.addEventListener("click", () => {
    resetCategoryForm();
    renderCategories();
  });
  nodes.resetProductButton.addEventListener("click", () => {
    resetProductForm();
    renderProducts();
  });
  nodes.resetBannerButton.addEventListener("click", () => {
    resetBannerForm();
    renderBanners();
  });
  nodes.addSizeButton.addEventListener("click", () => appendSizeOptionRow());
  nodes.addAddonButton.addEventListener("click", () => appendAddonOptionRow());

  nodes.productImageFile.addEventListener("change", () => {
    uploadImage(
      nodes.productImageFile.files?.[0],
      nodes.productMessage,
      (url) => applyUploadState({
        url,
        hiddenInput: productFormNodes.imageUrl,
        pathNode: nodes.productImagePath,
        previewNode: nodes.productImagePreview,
        fileNode: nodes.productImageFile,
      }),
      nodes.productImageFile,
    );
  });
  nodes.bannerImageFile.addEventListener("change", () => {
    uploadImage(
      nodes.bannerImageFile.files?.[0],
      nodes.bannerMessage,
      (url) => applyUploadState({
        url,
        hiddenInput: bannerFormNodes.imageUrl,
        pathNode: nodes.bannerImagePath,
        previewNode: nodes.bannerImagePreview,
        fileNode: nodes.bannerImageFile,
      }),
      nodes.bannerImageFile,
    );
  });

  nodes.clearProductImageButton.addEventListener("click", () => {
    applyUploadState({
      url: "",
      hiddenInput: productFormNodes.imageUrl,
      pathNode: nodes.productImagePath,
      previewNode: nodes.productImagePreview,
      fileNode: nodes.productImageFile,
    });
  });
  nodes.clearBannerImageButton.addEventListener("click", () => {
    applyUploadState({
      url: "",
      hiddenInput: bannerFormNodes.imageUrl,
      pathNode: nodes.bannerImagePath,
      previewNode: nodes.bannerImagePreview,
      fileNode: nodes.bannerImageFile,
    });
  });

  categoryFormNodes.name.addEventListener("input", () => {
    if (!categorySlugTouched && !categoryFormNodes.id.value) {
      categoryFormNodes.slug.value = slugify(categoryFormNodes.name.value);
    }
  });
  categoryFormNodes.slug.addEventListener("input", () => {
    categorySlugTouched = true;
  });

  loyaltyFormNodes.categoryOptions?.addEventListener("change", renderLoyaltyPreview);
  loyaltyFormNodes.paidItemsPerReward.addEventListener("input", renderLoyaltyPreview);
  loyaltyFormNodes.bonusEnabled.addEventListener("change", renderLoyaltyPreview);
  loyaltyFormNodes.bonusEarnPercent.addEventListener("input", renderLoyaltyPreview);
  loyaltyFormNodes.bonusRedeemEnabled.addEventListener("change", renderLoyaltyPreview);
  loyaltyFormNodes.bonusRedeemMaxPercent?.addEventListener("input", renderLoyaltyPreview);
  reminderFormNodes.enabled?.addEventListener("change", renderReminderPreview);
  reminderFormNodes.days?.addEventListener("input", renderReminderPreview);
  reminderFormNodes.sendTime?.addEventListener("input", renderReminderPreview);
  reminderFormNodes.text?.addEventListener("input", renderReminderPreview);
  nodes.analyticsLoadButton?.addEventListener("click", loadAnalytics);
  nodes.analyticsExportCsvButton?.addEventListener("click", () => {
    downloadWithSession(`/api/admin/analytics/export.csv${getAnalyticsQueryString()}`, "coffee-analytics.csv");
  });
  nodes.analyticsExportXlsxButton?.addEventListener("click", () => {
    downloadWithSession(`/api/admin/analytics/export.xlsx${getAnalyticsQueryString()}`, "coffee-analytics.xlsx");
  });
  nodes.analyticsRangeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const range = button.dataset.analyticsRange;
      if (range === "today") {
        setAnalyticsPreset(1);
      } else {
        setAnalyticsPreset(Number(range || 30));
      }
      if (state.activeTab === "analytics") {
        loadAnalytics();
      }
    });
  });

  productFormNodes.categoryId.addEventListener("change", () => {
    if (productFormNodes.id.value || productFormNodes.productType.value.trim()) {
      return;
    }
    const selected = state.categories.find((item) => String(item.id) === productFormNodes.categoryId.value);
    if (selected) {
      productFormNodes.productType.value = selected.slug;
    }
  });

  nodes.productFilterCategory.addEventListener("change", () => {
    state.filterCategory = nodes.productFilterCategory.value;
    renderProducts();
  });

  resetLoyaltyForm();
  resetAppSettingsForm();
  fillReminderForm(defaultReminderSettings());
  setAnalyticsPreset(30);
  resetBaristaForm();
  resetShiftForm();
  resetCategoryForm();
  resetProductForm();
  resetBannerForm();
  switchAdminTab(state.activeTab);
  loadDashboard();
}

window.addEventListener("DOMContentLoaded", init);

