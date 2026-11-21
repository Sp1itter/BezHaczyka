import { useMemo, useState } from "react";
import { RiskBadge } from "../common/Badge.jsx";
import StatusSelect from "./StatusSelect.jsx";
import { AssigneeTag } from "./Assignee.jsx";
import { SOURCE, fmtDate, publisherName } from "../../lib/labels.js";
import { sortFindings } from "../../lib/sort.js";

// Kolumny sortowalne (key z lib/sort.js); reszta bez sortowania.
const COLS = [
  { key: "date", label: "Data" },
  { key: "risk", label: "Ryzyko" },
  { key: "source", label: "Źródło" },
  { key: "module", label: "Moduły" },
  { key: "publisher", label: "Tytuł / publikujący" },
  { label: "Podmiot" },
  { label: "Przypisany" },
  { key: "status", label: "Status" },
];

export default function FindingsTable({ items, onOpen, onStatusChange, emptyText = "Brak wyników dla filtrów." }) {
  const [sort, setSort] = useState({ key: "risk", dir: "desc" });
  const rows = useMemo(() => sortFindings(items || [], sort.key, sort.dir), [items, sort]);
  if (!items?.length) return <div className="empty">{emptyText}</div>;
  const toggle = (key) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === "desc" ? "asc" : "desc" } : { key, dir: "desc" }));
  return (
    <table className="table">
      <thead>
        <tr>
          {COLS.map((c) =>
            c.key ? (
              <th key={c.label} className="sortable" aria-sort={sort.key === c.key ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}>
                <button type="button" className="sort-btn" onClick={() => toggle(c.key)}>
                  {c.label}{sort.key === c.key ? (sort.dir === "asc" ? " ▲" : " ▼") : ""}
                </button>
              </th>
            ) : (
              <th key={c.label}>{c.label}</th>
            )
          )}
        </tr>
      </thead>
      <tbody>
        {rows.map((f) => (
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
