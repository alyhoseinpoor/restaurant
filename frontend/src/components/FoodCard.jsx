import { resolveImage } from '../api';

export default function FoodCard({ food, onOpen }) {
  const imgUrl = resolveImage(food.img);

  return (
    <div className="food-card" onClick={() => onOpen(food)}>
      <div className="img-wrap">
        {imgUrl ? (
          <img src={imgUrl} alt={food.title} />
        ) : (
          <span className="no-img">بدون تصویر</span>
        )}
      </div>
      <div className="body">
        <h3>{food.title}</h3>
        <p className="desc">{food.desc}</p>
        <div className="price-row">
          <span>{Number(food.price).toLocaleString('fa-IR')} تومان</span>
          {!food.available && <span className="unavailable-badge">ناموجود</span>}
        </div>
      </div>
    </div>
  );
}
