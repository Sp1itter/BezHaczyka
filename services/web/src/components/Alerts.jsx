export default function Alerts({ alerts, onOpen }) {
  if (!alerts.length) return null;
  return (
    <div className="toasts" role="status" aria-live="polite">
      {alerts.map((a) => (
        <div key={a.finding_id + a.risk_score} className="toast" onClick={() => onOpen(a)}>
          <div className="risk high">Wysokie ryzyko · {a.risk_score.toFixed(1)}</div>
          <div className="clip">{a.title || a.document_id}</div>
          <div className="muted" style={{ fontSize: 12 }}>
            {a.source} · naruszone reguły: {a.failed_rules.join(", ") || "—"}
          </div>
        </div>
      ))}
    </div>
  );
}
