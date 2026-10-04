const BASE_URL = import.meta.env.VITE_API_BASE_URL;

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

// ---------- Foods ----------
export async function fetchFoods({ category, search } = {}) {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  if (search) params.set('search', search);
  const qs = params.toString() ? `?${params.toString()}` : '';
  const res = await apiFetch(`/api/foods/${qs}`);
  if (!res.ok) throw new Error('خطا در دریافت منو');
  return unwrap(await res.json());
}

// ---------- Categories ----------
export async function fetchCategories() {
  const res = await apiFetch('/api/categories/');
  if (!res.ok) throw new Error('خطا در دریافت دسته‌بندی‌ها');
  return unwrap(await res.json());
}

// ---------- Comments ----------
// توجه: بک‌اند کامنت‌ها رو بر اساس food فیلتر نمی‌کنه، پس همه‌ی کامنت‌های
// تأییدشده رو می‌گیریم و خودمون سمت کلاینت بر اساس food فیلتر می‌کنیم.
export async function fetchAllComments() {
  const res = await apiFetch('/api/comments/');
  if (!res.ok) throw new Error('خطا در دریافت نظرات');
  return unwrap(await res.json());
}

export async function createComment(foodId, text) {
  const res = await apiFetch('/api/comments/', {
    method: 'POST',
    body: JSON.stringify({ food: foodId, text }),
  });
  if (!res.ok) throw new Error('خطا در ثبت نظر');
  return res.json();
}

// ---------- Favorites ----------
export async function fetchFavorites() {
  const res = await apiFetch('/api/favorites/');
  if (!res.ok) throw new Error('خطا در دریافت علاقه‌مندی‌ها');
  return unwrap(await res.json());
}

export async function addFavorite(foodId) {
  const res = await apiFetch('/api/favorites/', {
    method: 'POST',
    body: JSON.stringify({ food: foodId }),
  });
  if (!res.ok) throw new Error('این آیتم قبلاً به علاقه‌مندی‌ها اضافه شده');
  return res.json();
}

// ---------- Orders (سبد خرید + سفارش‌های نهایی) ----------
export async function fetchOrders() {
  const res = await apiFetch('/api/orders/');
  if (!res.ok) throw new Error('خطا در دریافت سفارش‌ها');
  return unwrap(await res.json());
}

export async function addToCart(foodId) {
  const res = await apiFetch('/api/orders/', {
    method: 'POST',
    body: JSON.stringify({ food: foodId, number: 1 }),
  });
  if (!res.ok) throw new Error('خطا در افزودن به سبد خرید');
  return res.json();
}

export async function increaseOrder(id) {
  const res = await apiFetch(`/api/orders/${id}/increase/`, { method: 'POST' });
  if (!res.ok) throw new Error('خطا');
  return res.json();
}

export async function decreaseOrder(id) {
  const res = await apiFetch(`/api/orders/${id}/decrease/`, { method: 'POST' });
  if (!res.ok) throw new Error('خطا');
  return res.json();
}

export async function finalizeOrder(id) {
  const res = await apiFetch(`/api/orders/${id}/finalize/`, { method: 'POST' });
  if (!res.ok) throw new Error('خطا در نهایی کردن سفارش');
  return res.json();
}

export async function removeOrder(id) {
  const res = await apiFetch(`/api/orders/${id}/remove/`, { method: 'POST' });
  if (!res.ok) throw new Error('خطا در حذف سفارش');
  return res.json();
}

// DRF با pagination آرایه رو توی results می‌ذاره، بدون pagination خود آرایه‌ست
function unwrap(data) {
  return Array.isArray(data) ? data : data.results || [];
}
