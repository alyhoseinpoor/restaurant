import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './auth/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Menu from './pages/Menu';
import Cart from './pages/Cart';
import Orders from './pages/Orders';
import Favorites from './pages/Favorites';

// همه صفحات (چه لاگین باشی چه نه) این چیدمان مشترک با Navbar رو دارن
function Layout({ children }) {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="content">{children}</main>
    </div>
  );
}

// فقط برای صفحاتی که بک‌اند IsAuthenticated روشون گذاشته (سبد خرید، سفارش‌ها، علاقه‌مندی‌ها)
function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/menu" element={<Layout><Menu /></Layout>} />
      <Route
        path="/cart"
        element={<Layout><RequireAuth><Cart /></RequireAuth></Layout>}
      />
      <Route
        path="/orders"
        element={<Layout><RequireAuth><Orders /></RequireAuth></Layout>}
      />
      <Route
        path="/favorites"
        element={<Layout><RequireAuth><Favorites /></RequireAuth></Layout>}
      />
      <Route path="*" element={<Navigate to="/menu" replace />} />
    </Routes>
  );
}
