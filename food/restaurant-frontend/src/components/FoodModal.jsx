import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { resolveImage, fetchAllComments, createComment, addToCart, addFavorite } from '../api';
import { useAuth } from '../auth/AuthContext';

export default function FoodModal({ food, onClose }) {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [comments, setComments] = useState([]);
  const [loadingComments, setLoadingComments] = useState(isAuthenticated);
  const [commentText, setCommentText] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    if (!isAuthenticated) return; // دیدن نظرات هم نیاز به لاگین داره (بک‌اند IsAuthenticated)
    let alive = true;
    setLoadingComments(true);
    fetchAllComments()
      .then((all) => {
        if (alive) setComments(all.filter((c) => c.food === food.id));
      })
      .catch(() => {})
      .finally(() => alive && setLoadingComments(false));
    return () => { alive = false; };
  }, [food.id, isAuthenticated]);

  function goLogin() {
    onClose();
    navigate('/login');
  }

  async function handleAddToCart() {
    if (!isAuthenticated) return goLogin();
    setNotice('');
    try {
      await addToCart(food.id);
      setNotice('✅ به سبد خرید اضافه شد');
    } catch (err) {
      setNotice('❌ ' + err.message);
    }
  }

  async function handleFavorite() {
    if (!isAuthenticated) return goLogin();
    setNotice('');
    try {
      await addFavorite(food.id);
      setNotice('❤ به علاقه‌مندی‌ها اضافه شد');
    } catch (err) {
      setNotice('❌ ' + err.message);
    }
  }

  async function handleCommentSubmit(e) {
    e.preventDefault();
    if (!isAuthenticated) return goLogin();
    if (!commentText.trim()) return;
    try {
      await createComment(food.id, commentText);
      setCommentText('');
      setNotice('نظر شما ثبت شد و بعد از تأیید نمایش داده می‌شه');
    } catch (err) {
      setNotice('❌ ' + err.message);
    }
  }

  const imgUrl = resolveImage(food.img);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        {imgUrl && (
          <div className="img-wrap">
            <img src={imgUrl} alt={food.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
        )}

        <h2>{food.title}</h2>
        <p>{food.desc}</p>
        <p className="modal-price">{Number(food.price).toLocaleString('fa-IR')} تومان</p>

        <div className="modal-actions">
          <button className="btn-outline filled" onClick={handleAddToCart} disabled={!food.available}>
            افزودن به سبد خرید
          </button>
          <button className="btn-outline" onClick={handleFavorite}>
            ❤ علاقه‌مندی
          </button>
        </div>

        {notice && <p className="form-error" style={{ color: 'var(--maroon)' }}>{notice}</p>}

        <div className="section-title">نظرات{isAuthenticated ? ` (${comments.length})` : ''}</div>

        {!isAuthenticated ? (
          <p className="empty-note">
            برای دیدن و ثبت نظر باید{' '}
            <button className="link-btn" style={{ color: 'var(--maroon)' }} onClick={goLogin}>
              وارد بشی
            </button>
          </p>
        ) : loadingComments ? (
          <p className="empty-note">در حال بارگذاری نظرات...</p>
        ) : comments.length === 0 ? (
          <p className="empty-note">هنوز نظر تأییدشده‌ای برای این غذا ثبت نشده.</p>
        ) : (
          comments.map((c) => (
            <div className="comment-row" key={c.id}>
              <div className="who">
                {user && c.user === user.id ? 'شما' : `کاربر #${c.user}`}
              </div>
              <div>{c.text}</div>
            </div>
          ))
        )}

        {isAuthenticated && (
          <form className="comment-form" onSubmit={handleCommentSubmit}>
            <textarea
              rows={3}
              placeholder="نظرت رو درباره این غذا بنویس..."
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              required
            />
            <button className="btn-primary" type="submit">ثبت نظر</button>
          </form>
        )}
      </div>
    </div>
  );
}
