import { useEffect, useState } from 'react';
import { fetchOrders, fetchFoods } from '../api';

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [foodsById, setFoodsById] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([fetchOrders(), fetchFoods()])
      .then(([allOrders, foods]) => {
        setOrders(allOrders.filter((o) => o.active));
        setFoodsById(Object.fromEntries(foods.map((f) => [f.id, f])));
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="page-heading">سفارش‌های نهایی‌شده</h1>

      {loading && <p className="empty-note">در حال بارگذاری...</p>}
      {error && <p className="empty-note">{error}</p>}
      {!loading && !error && orders.length === 0 && (
        <p className="empty-note">هنوز سفارشی نهایی نکردی.</p>
      )}

      {orders.map((o) => {
        const food = foodsById[o.food];
        return (
          <div className="order-row" key={o.id}>
            <div>
              <div className="name">{food?.title || `آیتم #${o.food}`}</div>
              <div className="sub">تعداد: {o.number}</div>
            </div>
            <span className="status-badge">نهایی‌شده</span>
          </div>
        );
      })}
    </div>
  );
}
