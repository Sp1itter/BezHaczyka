// Kolumny tabel findingow w formie wzorca (table-title + table-meta, badge, status, tagi).
import { RiskBadge, StatusPill } from "../components/ui.jsx";
import { MODULE, fmtDate, publisherName, sourceLabel } from "../lib/labels.js";
import { num } from "../lib/ui.js";

const title = (f) => f.document?.title || f.document?.text_excerpt?.slice(0, 90) || "Bez tytułu";

export const COL = {
  date: { label: "Data", type: "date", className: "nowrap", sortValue: (f) => f.created_at, render: (f) => fmtDate(f.created_at) },
  title: {
    label: "Materiał", type: "text", className: "wide-cell", sortValue: title,
    render: (f) => (
      <>
        <a className="table-title" href={`#/findings/${encodeURIComponent(f.id)}`}>{title(f)}</a>
        <span className="table-meta">{[sourceLabel(f.document?.source), publisherName(f.document)].filter(Boolean).join(" · ")}</span>
      </>
    ),
  },
  modules: {
    label: "Moduły", type: "text", sortValue: (f) => (f.modules || []).join(","),
    render: (f) => (f.modules?.length
      ? <div className="tag-list">{f.modules.map((m) => <span className="tag" key={m} title={MODULE[m]}>M{m}</span>)}</div>
      : <span className="muted-value">—</span>),
  },
  violations: {
    label: "Naruszenia", type: "number", sortValue: (f) => (f.violations || []).length,
    render: (f) => (f.violations?.length
      ? <div className="tag-list">{f.violations.slice(0, 4).map((v) => <span className="tag" key={v.rule_id} title={v.rule_name}>{v.rule_id}</span>)}
          {f.violations.length > 4 && <span className="quiet">+{f.violations.length - 4}</span>}</div>
      : <span className="muted-value">—</span>),
  },
  risk: { label: "Poziom", type: "severity", sortValue: (f) => f.risk_level, render: (f) => <RiskBadge level={f.risk_level} /> },
  score: { label: "Wynik", type: "number", className: "nowrap", sortValue: (f) => f.risk_score, render: (f) => <span className="mono">{num(f.risk_score)}</span> },
  status: { label: "Status", type: "text", sortValue: (f) => f.status, render: (f) => <StatusPill status={f.status} /> },
  assignee: {
    label: "Przypisany", type: "text", sortValue: (f) => f.assignee || "",
    render: (f) => (f.assignee
      ? <>{f.assignee}{f.assigned_by === "ai" && <span className="table-meta">propozycja systemu</span>}</>
      : <span className="muted-value">—</span>),
  },
};
