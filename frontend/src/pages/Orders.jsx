import { useEffect, useState } from 'react';
import { fetchOrders, cancelOrder } from '../api';

const STATUS_LABELS = {
  placed: 'ثبت‌شده',
  preparing: 'در حال آماده‌سازی',
  delivered: 'تحویل داده شد',
  cancelled: 'لغو شده',
};

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setError('');
    try {
      setOrders(await fetchOrders());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCancel(id) {
    try {
      await cancelOrder(id);
      load();
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <div>
      <h1 className="page-heading">سفارش‌های من</h1>

      {loading && <p className="empty-note">در حال بارگذاری...</p>}
      {error && <p className="empty-note">{error}</p>}
      {!loading && !error && orders.length === 0 && (
        <p className="empty-note">هنوز سفارشی ثبت نکردی.</p>
      )}

      {orders.map((order) => (
        <div className="order-row" key={order.id}>
          <div>
            <div className="name">سفارش #{order.id}</div>
            <div className="sub">
              {order.items.map((i) => `${i.quantity}× ${i.food_title}`).join('، ')}
            </div>
            <div className="sub">
              جمع: {Number(order.total).toLocaleString('fa-IR')} تومان
            </div>
          </div>

          <div className="order-actions">
            <span className="status-badge">{STATUS_LABELS[order.status] || order.status}</span>
            {order.status === 'placed' && (
              <button className="btn-small remove" onClick={() => handleCancel(order.id)}>
                لغو سفارش
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
