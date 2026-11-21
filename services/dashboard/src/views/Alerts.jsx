import Panel from "../components/common/Panel.jsx";
import FindingsTable from "../components/findings/FindingsTable.jsx";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { fmtDate, SOURCE } from "../lib/labels.js";

// Kolejka alertow: wysokie ryzyko, nieobsluzone + strumien na zywo z WebSocket.
export default function Alerts({ query, reloadKey, live, feed, onOpen, onUpdate }) {
  const q = { ...query, risk_level: ["high"], status: query.status?.length ? query.status : ["new", "triage", "in_review"] };
  const list = useApi(() => api.findings(q), [JSON.stringify(q) + reloadKey]);
  return (
    <div className="grid">
      <Panel title={`Kolejka: wysokie ryzyko do obsłużenia (${list.data?.total ?? "…"})`} className="span-8">
        <FindingsTable items={list.data?.items} onOpen={onOpen} onStatusChange={onUpdate} emptyText="Brak otwartych alertów." />
      </Panel>
      <Panel title={`Na żywo ${live ? "●" : "○"}`} className="span-4">
        {!feed.length && <div className="empty">Czekam na alerty na żywo…</div>}
        <ul className="feed">
          {feed.map((a) => (
            <li key={a.finding_id} onClick={() => onOpen(a.finding_id)}>
              <span className="badge" style={{ background: "#e7664c" }}>{a.risk_score?.toFixed(1)}</span>
              <div>
                <div>{a.title}</div>
                <div className="muted">{SOURCE[a.source]} · M{a.primary_module} · {fmtDate(a.created_at)}</div>
              </div>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
