// Nawigacja boczna. items: [{ id, label, icon, badge? }]
export default function Sidebar({ items, active, onSelect, brand, footer }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-logo">{brand.logo}</span>
        <span className="brand-name">{brand.name}</span>
      </div>
      <nav>
        {items.map((it) => (
          <button key={it.id} className={`nav-item ${active === it.id ? "active" : ""}`} onClick={() => onSelect(it.id)}>
            <span className="nav-icon">{it.icon}</span>
            <span>{it.label}</span>
            {it.badge ? <span className="nav-badge">{it.badge}</span> : null}
          </button>
        ))}
      </nav>
      {footer && <div className="sidebar-footer">{footer}</div>}
    </aside>
  );
}
