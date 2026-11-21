// Filtrowanie i agregaty liczone w przegladarce na liscie z GET /findings.
// Dzieki temu panel dziala na obecnym services/api (bez /stats/trend i filtrow dat/list)
// oraz na mocku. Przy duzych wolumenach przeniesc to do SQL (patrz README, [DB-1], [DB-5]).

const asList = (v) => (v == null || v === "" ? [] : Array.isArray(v) ? v.map(String) : [String(v)]);

// Rekord zweryfikowany = jest decyzja czlowieka (review) albo status koncowy.
export const isReviewed = (f) => !!f.review || f.status === "confirmed" || f.status === "dismissed";

export function applyFilters(items, q = {}) {
  const risk = asList(q.risk_level), status = asList(q.status), source = asList(q.source), module = asList(q.module);
  const text = (q.q || "").toLowerCase();
  return items.filter((f) =>
    (!risk.length || risk.includes(f.risk_level)) &&
    (!status.length || status.includes(f.status)) &&
    (!source.length || source.includes(f.document?.source)) &&
    (!module.length || (f.modules || []).some((m) => module.includes(String(m)))) &&
    (!q.from || f.created_at >= q.from) &&
    (!q.to || f.created_at <= q.to) &&
    (q.min_score == null || f.risk_score >= Number(q.min_score)) &&
    (q.reviewed == null || String(isReviewed(f)) === String(q.reviewed)) &&
    (!text ||
      [f.document?.title, f.document?.publisher, f.routing?.reason, f.entities?.investment_firm?.name_in_ad]
        .join(" ").toLowerCase().includes(text)));
}

const count = (arr, key) => arr.reduce((acc, x) => ((acc[key(x)] = (acc[key(x)] || 0) + 1), acc), {});

export function stats(items) {
  const failed = {};
  for (const f of items)
    for (const r of f.rule_results || [])
      if (r.verdict === "fail") (failed[r.rule_id] ||= { rule_id: r.rule_id, rule_name: r.rule_name, count: 0 }).count++;
  return {
    total: items.length,
    by_risk_level: count(items, (f) => f.risk_level),
    by_status: count(items, (f) => f.status),
    by_source: count(items, (f) => f.document?.source || "?"),
    by_module: count(items.flatMap((f) => f.modules || []), (m) => String(m)),
    failed_rules: Object.values(failed).sort((a, b) => b.count - a.count),
  };
}

export function trend(items) {
  const days = {};
  for (const f of items) {
    const d = (f.created_at || "").slice(0, 10);
    days[d] ||= { date: d, high: 0, medium: 0, low: 0, total: 0 };
    days[d][f.risk_level] = (days[d][f.risk_level] || 0) + 1;
    days[d].total++;
  }
  return Object.values(days).sort((a, b) => a.date.localeCompare(b.date));
}
