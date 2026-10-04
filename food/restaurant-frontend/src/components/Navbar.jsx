import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

const TABS = [
  { to: '/menu', label: 'منو', private: false },
  { to: '/cart', label: 'سبد خرید', private: true },
  { to: '/orders', label: 'سفارش‌های نهایی', private: true },
  { to: '/favorites', label: 'علاقه‌مندی‌ها', private: true },
];

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <>
      <header className="top-bar">
        <div className="brand">سفره‌<span>خانه</span></div>
        <div className="user-chip">
          {isAuthenticated ? (
            <>
              {user?.username && <span>{user.username}</span>}
              <button className="link-btn" onClick={logout}>خروج</button>
            </>
          ) : (
            <NavLink className="link-btn" to="/login">ورود</NavLink>
          )}
        </div>
      </header>
      <nav className="tabs-bar">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.private && !isAuthenticated ? '/login' : t.to}
            className={({ isActive }) => 'tab-link' + (isActive ? ' active' : '')}
          >
            {t.label}{t.private && !isAuthenticated ? ' 🔒' : ''}
          </NavLink>
        ))}
      </nav>
    </>
  );
}
