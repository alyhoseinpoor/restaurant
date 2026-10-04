import { useEffect, useState } from 'react';
import { fetchFavorites, fetchFoods, resolveImage } from '../api';

export default function Favorites() {
  const [favorites, setFavorites] = useState([]);
  const [foodsById, setFoodsById] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([fetchFavorites(), fetchFoods()])
      .then(([favs, foods]) => {
        setFavorites(favs);
        setFoodsById(Object.fromEntries(foods.map((f) => [f.id, f])));
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="page-heading">علاقه‌مندی‌های من</h1>

      {loading && <p className="empty-note">در حال بارگذاری...</p>}
      {error && <p className="empty-note">{error}</p>}
      {!loading && !error && favorites.length === 0 && (
        <p className="empty-note">چیزی به علاقه‌مندی‌ها اضافه نکردی.</p>
      )}

      <div className="food-grid">
        {favorites.map((fav) => {
          const food = foodsById[fav.food];
          if (!food) return null;
          const imgUrl = resolveImage(food.img);
          return (
            <div className="food-card" key={fav.id}>
              <div className="img-wrap">
                {imgUrl ? <img src={imgUrl} alt={food.title} /> : <span className="no-img">بدون تصویر</span>}
              </div>
              <div className="body">
                <h3>{food.title}</h3>
                <div className="price-row">
                  <span>{Number(food.price).toLocaleString('fa-IR')} تومان</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
