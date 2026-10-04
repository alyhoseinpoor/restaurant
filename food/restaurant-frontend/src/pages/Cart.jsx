import { useEffect, useState } from 'react';
import { fetchOrders, fetchFoods, increaseOrder, decreaseOrder, finalizeOrder, removeOrder } from '../api';

export default function Cart() {
  const [orders, setOrders] = useState([]);
  const [foodsById, setFoodsById] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [allOrders, foods] = await Promise.all([fetchOrders(), fetchFoods()]);
      setOrders(allOrders.filter((o) => !o.active));
      setFoodsById(Object.fromEntries(foods.map((f) => [f.id, f])));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleAction(fn, id) {
    try {
      await fn(id);
      load();
    } catch (err) {
      alert(err.message);
    }
  }

  const total = orders.reduce((sum, o) => {
    const food = foodsById[o.food];
    return sum + (food ? food.price * o.number : 0);
  }, 0);

  return (
    <div>
      <h1 className="page-heading">سبد خرید</h1>

      {loading && <p className="empty-note">در حال بارگذاری...</p>}
      {error && <p className="empty-note">{error}</p>}
      {!loading && !error && orders.length === 0 && (
        <p className="empty-note">سبد خریدت خالیه — از منو چیزی اضافه کن.</p>
      )}

      {orders.map((o) => {
        const food = foodsById[o.food];
        return (
          <div className="order-row" key={o.id}>
            <div>
              <div className="name">{food?.title || `آیتم #${o.food}`}</div>
              <div className="sub">{food ? Number(food.price).toLocaleString('fa-IR') + ' تومان' : ''}</div>
            </div>

            <div className="qty-control">
              <button onClick={() => handleAction(decreaseOrder, o.id)}>−</button>
              <span>{o.number}</span>
              <button onClick={() => handleAction(increaseOrder, o.id)}>+</button>
            </div>

            <div className="order-actions">
              <button className="btn-small finalize" onClick={() => handleAction(finalizeOrder, o.id)}>
                نهایی کردن
              </button>
              <button className="btn-small remove" onClick={() => handleAction(removeOrder, o.id)}>
                حذف
              </button>
            </div>
          </div>
        );
      })}

      {orders.length > 0 && (
        <div className="cart-summary">
          <span>جمع کل</span>
          <span>{total.toLocaleString('fa-IR')} تومان</span>
        </div>
      )}
    </div>
  );
}
