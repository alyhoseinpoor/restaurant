const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ---------- مدیریت توکن ----------
export function getTokens() {
  return {
    access: localStorage.getItem('access'),
    refresh: localStorage.getItem('refresh'),
  };
}

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem('access', access);
  if (refresh) localStorage.setItem('refresh', refresh);
}

export function clearTokens() {
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
}

// از payload توکن (بدون کتابخونه) شناسه و username کاربر رو می‌خونیم
export function decodeToken(token) {
  try {
    const payload = token.split('.')[1];
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

async function refreshAccessToken() {
  const { refresh } = getTokens();
  if (!refresh) return false;
  const res = await fetch(`${BASE_URL}/api/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  setTokens({ access: data.access });
  return true;
}

// ---------- fetch عمومی ----------
export async function apiFetch(path, options = {}) {
  const { access } = getTokens();
  const headers = { ...(options.headers || {}) };
  if (access) headers['Authorization'] = `Bearer ${access}`;
  if (options.body) headers['Content-Type'] = 'application/json';

  let res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    const ok = await refreshAccessToken();
    if (ok) {
      const { access: newAccess } = getTokens();
      headers['Authorization'] = `Bearer ${newAccess}`;
      res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
    }
  }
  return res;
}

// پیام خطای بک‌اند را می‌خواند: {"detail": "..."} یا {"field": ["..."]}
async function readError(res, fallback) {
  try {
    const data = await res.json();
    if (typeof data === 'string') return data;
    if (data.detail) return String(data.detail);
    const messages = Object.values(data).flat().map(String);
    if (messages.length) return messages.join(' ');
  } catch {
    // بدنه JSON نبود؛ پیام پیش‌فرض
  }
  return fallback;
}

async function requestJson(path, options, fallback) {
  const res = await apiFetch(path, options);
  if (!res.ok) throw new Error(await readError(res, fallback));
  return res.status === 204 ? null : res.json();
}

// بک‌اند صفحه‌بندی دارد (۱۰ تا در هر صفحه)؛ همه صفحه‌ها را پشت سر هم می‌گیریم
async function fetchAll(path, fallback) {
  const items = [];
  let url = path;
  while (url) {
    const data = await requestJson(url, undefined, fallback);
    if (Array.isArray(data)) return data;
    items.push(...(data.results || []));
    if (data.next) {
      const next = new URL(data.next);
      url = next.pathname + next.search;
    } else {
      url = null;
    }
  }
  return items;
}

// آدرس کامل عکس (چون img ممکنه مسیر نسبی برگرده)
export function resolveImage(url) {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${BASE_URL}${url}`;
}

// ---------- Auth ----------
export async function login(username, password) {
  const res = await fetch(`${BASE_URL}/api/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error('نام کاربری یا رمز عبور اشتباهه');
  return res.json(); // { access, refresh }
}

export async function register(username, password) {
  const res = await fetch(`${BASE_URL}/api/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(await readError(res, 'ثبت‌نام انجام نشد'));
  return res.json();
}

// ---------- Foods & Categories ----------
export function fetchFoods({ category, search } = {}) {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  if (search) params.set('search', search);
  const qs = params.toString() ? `?${params.toString()}` : '';
  return fetchAll(`/api/foods/${qs}`, 'خطا در دریافت منو');
}

export function fetchCategories() {
  return fetchAll('/api/categories/', 'خطا در دریافت دسته‌بندی‌ها');
}

// ---------- Comments ----------
// فقط نظرهای تأییدشده‌ی همین غذا (فیلتر سمت بک‌اند)
export function fetchComments(foodId) {
  return fetchAll(`/api/comments/?food=${foodId}`, 'خطا در دریافت نظرات');
}

export function createComment(foodId, text) {
  return requestJson(
    '/api/comments/',
    { method: 'POST', body: JSON.stringify({ food: foodId, text }) },
    'خطا در ثبت نظر',
  );
}

// ---------- Favorites ----------
export function fetchFavorites() {
  return fetchAll('/api/favorites/', 'خطا در دریافت علاقه‌مندی‌ها');
}

export function addFavorite(foodId) {
  return requestJson(
    '/api/favorites/',
    { method: 'POST', body: JSON.stringify({ food: foodId }) },
    'خطا در افزودن به علاقه‌مندی‌ها',
  );
}

export function removeFavorite(id) {
  return requestJson(`/api/favorites/${id}/`, { method: 'DELETE' }, 'خطا در حذف علاقه‌مندی');
}

// ---------- Cart ----------
// پاسخ: { id, status, items: [{id, food, food_title, quantity, unit_price, subtotal}], total }
export function fetchCart() {
  return requestJson('/api/cart/', undefined, 'خطا در دریافت سبد خرید');
}

export function addToCart(foodId, quantity = 1) {
  return requestJson(
    '/api/cart/items/',
    { method: 'POST', body: JSON.stringify({ food: foodId, quantity }) },
    'خطا در افزودن به سبد خرید',
  );
}

export function setCartItemQuantity(itemId, quantity) {
  return requestJson(
    `/api/cart/items/${itemId}/`,
    { method: 'PATCH', body: JSON.stringify({ quantity }) },
    'خطا در تغییر تعداد',
  );
}

export function removeCartItem(itemId) {
  return requestJson(`/api/cart/items/${itemId}/`, { method: 'DELETE' }, 'خطا در حذف از سبد');
}

export function clearCart() {
  return requestJson('/api/cart/', { method: 'DELETE' }, 'خطا در خالی کردن سبد');
}

export function checkout() {
  return requestJson('/api/cart/checkout/', { method: 'POST' }, 'خطا در ثبت سفارش');
}

// ---------- Orders (سفارش‌های ثبت‌شده) ----------
export function fetchOrders() {
  return fetchAll('/api/orders/', 'خطا در دریافت سفارش‌ها');
}

export function cancelOrder(id) {
  return requestJson(`/api/orders/${id}/cancel/`, { method: 'POST' }, 'خطا در لغو سفارش');
}
