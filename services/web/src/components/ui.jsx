// Komponenty wzorca PRAKTYKI (te same klasy CSS i zachowania) dla danych InvestWatch.
import { useState } from "react";
import { RISK_TEXT, firstDirection, riskClass, sortRows, statusClass } from "../lib/ui.js";
import { STATUS } from "../lib/labels.js";
import { navigate } from "../lib/router.js";

export function RiskBadge({ level }) {
  return <span className={`badge ${riskClass(level)}`}>{RISK_TEXT[level] || "—"}</span>;
}

export function StatusPill({ status, children }) {
  return <span className={`status ${statusClass(status)}`}>{children || STATUS[status] || status || "—"}</span>;
}

export function PageHeader({ title, lead, actions }) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        {lead && <p className="page-lead">{lead}</p>}
      </div>
      <div className="page-actions">{actions}</div>
    </header>
  );
}

export function EmptyState({ title = "Brak wyników", children, size = "" }) {
  return (
    <div className={`empty-state ${size}`}>
      <strong>{title}</strong>
      {children && <p>{children}</p>}
    </div>
  );
}

export function ErrorState({ message }) {
  return (
    <section className="panel">
      <div className="empty-state large">
        <strong>Nie można wyświetlić tej pozycji</strong>
        <p>{message}</p>
        <a className="button secondary" href="#/">Wróć do przeglądu</a>
      </div>
    </section>
  );
}

// "Kopiuj" -> "Skopiowano" na 1,2 s, jak data-copy we wzorcu.
export function CopyButton({ value, onFail }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      onFail?.("Przeglądarka nie pozwoliła skopiować wartości.");
    }
  };
  return (
    <button type="button" className={`copy-button ${copied ? "is-copied" : ""}`} onClick={copy}>
      {copied ? "Skopiowano" : "Kopiuj"}
    </button>
  );
}

// Lista zwijana do `limit` pozycji z "Pokaz wiecej (N)" / "Zwin" (data-collapse-limit wzorca).
export function useCollapse(items, limit) {
  const [expanded, setExpanded] = useState(false);
  const hidden = limit ? Math.max(items.length - limit, 0) : 0;
  const visible = !limit || expanded ? items : items.slice(0, limit);
  const footer = hidden > 0 && (
    <div className="collapse-footer">
      <button type="button" className="button ghost small collapse-toggle" aria-expanded={expanded}
        onClick={() => setExpanded((e) => !e)}>
        {expanded ? "Zwiń" : `Pokaż więcej (${hidden})`}
      </button>
    </div>
  );
  return { visible, footer };
}

/**
 * Tabela sortowana kliknieciem naglowka (sort-button + sort-indicator + aria-sort).
 * columns: [{ label, type: "text"|"date"|"severity"|"number", sortValue(row), render(row), className }]
 */
export function SortableTable({ columns, rows, rowKey, collapseLimit, className = "", empty }) {
  const [sort, setSort] = useState({ index: null, direction: "asc" });
  const active = sort.index == null ? null : columns[sort.index];
  const sorted = sortRows(rows, active, sort.direction);
  const { visible, footer } = useCollapse(sorted, collapseLimit);
  const toggle = (i) =>
    setSort((s) => (s.index === i
      ? { index: i, direction: s.direction === "asc" ? "desc" : "asc" }
      : { index: i, direction: firstDirection(columns[i].type) }));
  if (!rows.length) return empty || <EmptyState size="compact">Zmień filtry albo poczekaj na kolejne analizy.</EmptyState>;
  return (
    <>
      <div className="table-wrap">
        <table className={className} data-sortable>
          <thead>
            <tr>
              {columns.map((c, i) => {
                const state = sort.index === i ? sort.direction : null;
                return (
                  <th key={c.label} aria-sort={state === "asc" ? "ascending" : state === "desc" ? "descending" : "none"}>
                    {c.sortValue ? (
                      <button type="button" className={`sort-button ${state ? `is-sorted-${state}` : ""}`}
                        title="Kliknij, aby sortować" onClick={() => toggle(i)}>
                        {c.label}<span className="sort-indicator" aria-hidden="true" />
                      </button>
                    ) : c.label}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {visible.map((row) => (
              <tr key={rowKey(row)}>
                {columns.map((c) => <td key={c.label} className={c.className}>{c.render(row)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {footer}
    </>
  );
}

/**
 * Szuflada filtrow wzorca (<details class="filter-drawer">): otwarta, gdy filtry aktywne,
 * kropka "aktywne", Zastosuj / Wyczysc. Stan filtrow zyje w adresie (path + query).
 * fields: [{ name, label, type: "search"|"select"|"date", options?: {value: label}, placeholder? }]
 */
export function FilterDrawer({ title = "Filtry", path, query, fields, resultCount }) {
  const active = fields.some((f) => query[f.name]);
  return (
    <details className="filter-drawer" open={active || undefined} key={JSON.stringify(query)}>
      <summary className="filter-drawer-summary">
        <span className="filter-drawer-label">
          <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M4 6h16M7 12h10M10 18h4" /></svg>
          {title}
        </span>
        {active
          ? <><span className="filter-active-dot" title="Filtry aktywne" /><span className="quiet">aktywne{resultCount != null ? ` · ${resultCount} wyników` : ""}</span></>
          : <span className="quiet">opcjonalne</span>}
        <span className="filter-chevron" aria-hidden="true" />
      </summary>
      <FilterForm className="filter-drawer-body" path={path} query={query} fields={fields}
        actions={(clear) => (
          <div className="filter-drawer-actions">
            <button className="button primary" type="submit">Zastosuj</button>
            {active && <button className="button ghost" type="button" onClick={clear}>Wyczyść</button>}
          </div>
        )} />
    </details>
  );
}

// Pasek filtrow w linii (alerts.html): te same pola, przycisk "Filtruj".
export function FilterBar({ path, query, fields, submitLabel = "Filtruj" }) {
  return (
    <FilterForm className="filter-bar" path={path} query={query} fields={fields}
      actions={() => <button className="button primary" type="submit">{submitLabel}</button>} />
  );
}

function FilterForm({ className, path, query, fields, actions }) {
  const submit = (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    navigate(path, data);
  };
  const clear = () => navigate(path, {});
  return (
    <form className={className} onSubmit={submit} key={JSON.stringify(query)}>
      {fields.map((f) => (
        <label key={f.name} className={f.type === "search" ? "search-field" : undefined}>
          <span>{f.label}</span>
          {f.type === "select" ? (
            <select name={f.name} defaultValue={query[f.name] || ""}>
              <option value="">Wszystkie</option>
              {Object.entries(f.options).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          ) : (
            <input type={f.type} name={f.name} defaultValue={query[f.name] || ""} placeholder={f.placeholder} />
          )}
        </label>
      ))}
      {actions(clear)}
    </form>
  );
}
