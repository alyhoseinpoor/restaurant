export default function CategoryFilter({ categories, activeSlug, onSelect, search, onSearch }) {
  return (
    <div className="filters-row">
      <button
        className={'chip' + (!activeSlug ? ' active' : '')}
        onClick={() => onSelect(null)}
      >
        همه
      </button>
      {categories.map((c) => (
        <button
          key={c.id}
          className={'chip' + (activeSlug === c.slug ? ' active' : '')}
          onClick={() => onSelect(c.slug)}
        >
          {c.name}
        </button>
      ))}
      <input
        className="search-input"
        placeholder="جستجوی غذا..."
        value={search}
        onChange={(e) => onSearch(e.target.value)}
      />
    </div>
  );
}
