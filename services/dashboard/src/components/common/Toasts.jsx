// Powiadomienia o alertach wysokiego ryzyka.
export default function Toasts({ items, onOpen, onDismiss }) {
  return (
    <div className="toasts">
      {items.map((t) => (
        <div key={t.finding_id} className="toast">
          <strong>Wysokie ryzyko · {t.risk_score?.toFixed(1)}</strong>
          <div>{t.title}</div>
          <div className="muted">{t.routing_reason}</div>
          <div className="toast-actions">
            <button className="btn primary" onClick={() => onOpen(t.finding_id)}>Otwórz</button>
            <button className="btn link" onClick={() => onDismiss(t.finding_id)}>Zamknij</button>
          </div>
        </div>
      ))}
    </div>
  );
}
