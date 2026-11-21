import { api } from "../../api/client.js";
import { useApi } from "../../hooks/useApi.js";
import { STATUS, fmtDate } from "../../lib/labels.js";

const describe = (e) => {
  const d = e.detail || {};
  if (e.action === "assign") return d.assignee ? `przypisano: ${d.assignee}` : "zwolniono przypisanie";
  if (e.action === "review") return `ocena: ${d.label}${d.note ? ` („${d.note}”)` : ""}`;
  if (e.action === "status") return `status: ${STATUS[d.status] || d.status}`;
  return e.action;
};

// Historia pracy nad rekordem z finding_events.
export default function Timeline({ finding: f }) {
  const ev = useApi(() => api.events(f.id), [f.id, f.status, f.assignee, f.review?.at]);
  const items = ev.data?.items || [];
  return (
    <ul className="timeline">
      <li><span className="muted">{fmtDate(f.created_at)}</span> wykrycie przez analyzer</li>
      {items.map((e, i) => (
        <li key={i}><span className="muted">{fmtDate(e.at)}</span> {e.actor ? <strong>{e.actor}</strong> : "system"}: {describe(e)}</li>
      ))}
      {ev.error && <li className="muted">Historia niedostępna ({ev.error.message})</li>}
    </ul>
  );
}
