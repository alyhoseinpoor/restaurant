import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { register } from '../api';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const isRegister = mode === 'register';

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) await register(username, password);
      await login(username, password);
      navigate('/menu');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function toggleMode() {
    setError('');
    setMode(isRegister ? 'login' : 'register');
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <h1>سفره‌خانه</h1>
        <p className="subtitle">
          {isRegister ? 'یه حساب بساز تا بتونی سفارش بدی' : 'برای مشاهده و ثبت سفارش وارد شو'}
        </p>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="username">نام کاربری</label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">رمز عبور</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="form-error">{error}</p>}
          <button className="btn-primary" disabled={loading}>
            {loading ? 'لطفاً صبر کن...' : isRegister ? 'ثبت‌نام' : 'ورود'}
          </button>
        </form>

        <p className="login-hint">
          {isRegister ? 'حساب داری؟ ' : 'حساب نداری؟ '}
          <button type="button" className="link-btn" onClick={toggleMode}>
            {isRegister ? 'وارد شو' : 'ثبت‌نام کن'}
          </button>
        </p>
      </div>
    </div>
  );
}
