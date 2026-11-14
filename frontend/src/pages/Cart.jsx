import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  fetchCart,
  setCartItemQuantity,
  removeCartItem,
  clearCart,
  checkout,
} from '../api';

const MAX_QUANTITY = 50; // هم‌خوان با بک‌اند

export default function Cart() {
  const navigate = useNavigate();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    setError('');
    try {
      setCart(await fetchCart());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  // هر عملیات: قفل دکمه‌ها، اجرا، دوباره گرفتن سبد
  async function run(action) {
    setBusy(true);
    try {
      await action();
      await load();
    } catch (err) {
      alert(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleCheckout() {
    setBusy(true);
    try {
      await checkout();
      navigate('/orders');
    } catch (err) {
      alert(err.message);
      setBusy(false);
    }
  }

  const items = cart?.items || [];

  return (
    <div>
      <h1 className="page-heading">سبد خرید</h1>

      {loading && <p className="empty-note">در حال بارگذاری...</p>}
      {error && <p className="empty-note">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="empty-note">سبد خریدت خالیه — از منو چیزی اضافه کن.</p>
      )}

      {items.map((item) => (
        <div className="order-row" key={item.id}>
          <div>
            <div className="name">{item.food_title}</div>
            <div className="sub">{Number(item.unit_price).toLocaleString('fa-IR')} تومان</div>
          </div>

          <div className="qty-control">
            <button
              disabled={busy}
              onClick={() =>
                run(() =>
                  item.quantity > 1
                    ? setCartItemQuantity(item.id, item.quantity - 1)
                    : removeCartItem(item.id),
                )
              }
            >
              −
            </button>
            <span>{item.quantity}</span>
            <button
              disabled={busy || item.quantity >= MAX_QUANTITY}
              onClick={() => run(() => setCartItemQuantity(item.id, item.quantity + 1))}
            >
              +
            </button>
          </div>

          <div className="order-actions">
            <span className="sub">{Number(item.subtotal).toLocaleString('fa-IR')} تومان</span>
            <button
              className="btn-small remove"
              disabled={busy}
              onClick={() => run(() => removeCartItem(item.id))}
            >
              حذف
            </button>
          </div>
        </div>
      ))}

      {items.length > 0 && (
        <>
          <div className="cart-summary">
            <span>جمع کل</span>
            <span>{Number(cart.total).toLocaleString('fa-IR')} تومان</span>
          </div>
          <div className="order-actions" style={{ marginTop: 16 }}>
            <button className="btn-small finalize" disabled={busy} onClick={handleCheckout}>
              ثبت سفارش
            </button>
            <button className="btn-small remove" disabled={busy} onClick={() => run(clearCart)}>
              خالی کردن سبد
            </button>
          </div>
        </>
      )}
    </div>
  );
}
