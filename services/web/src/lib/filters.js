// Filtry z adresu (#/sciezka?risk=high&...) -> parametry GET /findings, /stats, /stats/trend.
// Warunki laczone przez AND; filtrowanie robi services/api.

export const OPEN_STATUSES = ["new", "triage", "in_review"];
export const isOpen = (f) => OPEN_STATUSES.includes(f.status);

export function toApiFilters(q = {}) {
  return {
    q: q.q || undefined,
    risk_level: q.risk || undefined,
    module: q.module || undefined,
    status: q.status || undefined,
    source: q.source || undefined,
    from: q.from ? `${q.from}T00:00:00Z` : undefined,
    to: q.to ? `${q.to}T23:59:59Z` : undefined,
  };
}
