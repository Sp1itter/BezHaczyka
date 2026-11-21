// Panel wysuwany z prawej (szczegoly rekordu).
export default function Flyout({ open, title, onClose, children }) {
  if (!open) return null;
  return (
    <div className="flyout-backdrop" onClick={onClose}>
      <aside className="flyout" onClick={(e) => e.stopPropagation()}>
        <div className="flyout-head">
          <h2>{title}</h2>
          <button className="btn link" onClick={onClose}>✕</button>
        </div>
        <div className="flyout-body">{children}</div>
      </aside>
    </div>
  );
}
