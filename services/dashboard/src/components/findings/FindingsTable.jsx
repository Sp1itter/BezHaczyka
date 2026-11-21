import { RiskBadge } from "../common/Badge.jsx";
import StatusSelect from "./StatusSelect.jsx";
import { AssigneeTag } from "./Assignee.jsx";
import { SOURCE, fmtDate, publisherName } from "../../lib/labels.js";

// Tabela rekordow. columns sterowane z zewnatrz nie sa potrzebne w placeholderze.
export default function FindingsTable({ items, onOpen, onStatusChange, emptyText = "Brak wyników dla filtrów." }) {
  if (!items?.length) return <div className="empty">{emptyText}</div>;
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Data</th><th>Ryzyko</th><th>Źródło</th><th>Moduły</th><th>Tytuł / publikujący</th><th>Podmiot</th><th>Przypisany</th><th>Status</th>
        </tr>
      </thead>
      <tbody>
        {items.map((f) => (
          <tr key={f.id} onClick={() => onOpen(f.id)}>
            <td className="nowrap">{fmtDate(f.created_at)}</td>
            <td><RiskBadge level={f.risk_level} score={f.risk_score} /></td>
            <td>{SOURCE[f.document?.source] || f.document?.source}</td>
            <td>{f.modules.map((m) => `M${m}`).join(", ")}</td>
            <td>
              <div className="cell-title">{f.document?.title}</div>
              <div className="muted">{publisherName(f.document)}</div>
            </td>
            <td>
              {f.entities?.investment_firm?.name_in_ad}
              {f.entities?.investment_firm?.is_authorized === false && <span className="tag warn">poza KNF</span>}
            </td>
            <td><AssigneeTag finding={f} /></td>
            <td><StatusSelect value={f.status} onChange={(s) => onStatusChange(f.id, { status: s })} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
