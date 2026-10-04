import { useEffect, useState } from 'react';
import { fetchFoods, fetchCategories } from '../api';
import CategoryFilter from '../components/CategoryFilter';
import FoodCard from '../components/FoodCard';
import FoodModal from '../components/FoodModal';

export default function Menu() {
  const [foods, setFoods] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeSlug, setActiveSlug] = useState(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedFood, setSelectedFood] = useState(null);

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError('');
    const timeout = setTimeout(() => {
      fetchFoods({ category: activeSlug, search })
        .then(setFoods)
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }, 250); // debounce برای جستجو
    return () => clearTimeout(timeout);
  }, [activeSlug, search]);

  return (
    <div>
      <h1 className="page-heading">منوی رستوران</h1>

      <CategoryFilter
        categories={categories}
        activeSlug={activeSlug}
        onSelect={setActiveSlug}
        search={search}
        onSearch={setSearch}
      />

      {loading && <p className="empty-note">در حال بارگذاری...</p>}
      {error && <p className="empty-note">{error}</p>}
      {!loading && !error && foods.length === 0 && (
        <p className="empty-note">غذایی با این مشخصات پیدا نشد.</p>
      )}

      <div className="food-grid">
        {foods.map((food) => (
          <FoodCard key={food.id} food={food} onOpen={setSelectedFood} />
        ))}
      </div>

      {selectedFood && (
        <FoodModal food={selectedFood} onClose={() => setSelectedFood(null)} />
      )}
    </div>
  );
}
