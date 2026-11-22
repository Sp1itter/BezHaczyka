// Logika strony Wyniki bez JSX (testowalna w node --test).

export const PAGE_SIZES = [25, 50, 100];

/** Filtry z adresu (#/wyniki?from=...&risk=...) -> parametry GET /findings i /stats/trend. */
export function apiFilters(q = {}) {
  return {
    from: q.from ? `${q.from}T00:00:00Z` : undefined,
    to: q.to ? `${q.to}T23:59:59Z` : undefined,
    risk_level: q.risk || undefined,
    module: q.module || undefined,
    status: q.status || undefined,
    source: q.source || undefined,
    q: q.q || undefined,
  };
}

export function pageParams(q = {}) {
  const size = PAGE_SIZES.includes(Number(q.size)) ? Number(q.size) : 50;
  const page = Math.max(0, Number(q.page) || 0);
  return { pageIndex: page, pageSize: size, limit: size, offset: page * size };
}

const SEVERITY_FIRST = (a, b) => (b.severity ?? 0) - (a.severity ?? 0);

/** Reguly do szuflady: naruszenia na gorze (waga malejaco), potem do weryfikacji, spelnione, nieocenione. */
export function groupRules(rules = []) {
  const by = (v) => rules.filter((r) => r.verdict === v);
  return {
    failed: by("fail").sort(SEVERITY_FIRST),
    uncertain: by("uncertain").sort(SEVERITY_FIRST),
    passed: by("pass"),
    notAssessed: by("not_applicable"),
  };
}

/** Wartosc komorki CSV: cudzyslowy i ochrona przed formula w arkuszu (CSV injection). */
export function csvCell(v) {
  let s = v == null ? "" : String(v);
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`;
  return /[";\n,]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function toCsv(rows, columns) {
  const head = columns.map((c) => csvCell(c.label)).join(";");
  const body = rows.map((r) => columns.map((c) => csvCell(c.value(r))).join(";"));
  return [head, ...body].join("\r\n");
}
