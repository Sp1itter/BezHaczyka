// Mapowanie domeny InvestWatch na klasy komponentow wzorca (badge/status) i porownania sortowania.
// Bez JSX, testowalne.

export const RISK_TEXT = { high: "WYSOKIE", medium: "ŚREDNIE", low: "NISKIE" };
export const riskClass = (level) => (["high", "medium", "low"].includes(level) ? level : "neutral");

// Status findingu -> klasa .status.* wzorca (zamkniety zbior, jak status_class w PRAKTYKI).
const STATUS_CLASS = { new: "new", triage: "pending", in_review: "processing", confirmed: "approved", dismissed: "false_positive" };
export const statusClass = (s) => STATUS_CLASS[s] || "neutral";

// Kolejnosc jak SEVERITY_RANK wzorca: najwyzsze ryzyko pierwsze przy sortowaniu rosnacym.
const SEVERITY_RANK = { high: 1, medium: 2, low: 3 };

export function compareValues(a, b, type) {
  if (type === "number") return (Number(a) || 0) - (Number(b) || 0);
  if (type === "date") return (Date.parse(a || "") || 0) - (Date.parse(b || "") || 0);
  if (type === "severity") return (SEVERITY_RANK[a] || 99) - (SEVERITY_RANK[b] || 99);
  return String(a ?? "").localeCompare(String(b ?? ""), "pl", { sensitivity: "base", numeric: true });
}

// Pierwszy klik: data malejaco, reszta rosnaco (zachowanie sort-button wzorca).
export const firstDirection = (type) => (type === "date" ? "desc" : "asc");

export function sortRows(rows, column, direction) {
  if (!column) return rows;
  const factor = direction === "desc" ? -1 : 1;
  return rows
    .map((row, i) => ({ row, i }))
    .sort((x, y) => factor * compareValues(column.sortValue(x.row), column.sortValue(y.row), column.type) || x.i - y.i)
    .map((e) => e.row);
}

export const shortId = (id) => String(id || "").slice(0, 8).toUpperCase();
export const pct = (x) => (x == null || Number.isNaN(x) ? "—" : `${Math.round(x * 100)}%`);
export const num = (x, d = 1) => (x == null ? "—" : Number(x).toFixed(d).replace(".", ","));
