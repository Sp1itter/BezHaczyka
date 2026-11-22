// Sortowanie listy: stabilne, null/puste zawsze na koncu.
const RISK_RANK = { high: 3, medium: 2, low: 1 };

const text = (v) => (v == null || v === "" ? null : String(v).toLocaleLowerCase("pl"));
const publisher = (f) => {
  const p = f.document?.publisher;
  return typeof p === "string" ? p : p?.display_name || p?.handle || p?.name || null;
};
const time = (f) => (f.created_at ? Date.parse(f.created_at) : null);

// Lista kluczy porownania (rosnaco); kolejne rozstrzygaja remisy.
const KEYS = {
  risk: (f) => [RISK_RANK[f.risk_level] ?? null, f.risk_score ?? null],
  score: (f) => [f.risk_score ?? null],
  date: (f) => [time(f)],
  source: (f) => [text(f.document?.source)],
  module: (f) => [f.primary_module ?? null],
  status: (f) => [text(f.status)],
  publisher: (f) => [text(publisher(f))],
};

const cmp = (a, b) => (typeof a === "string" ? a.localeCompare(b, "pl") : a - b);

export function sortFindings(items, key, dir = "desc") {
  const keyFn = KEYS[key];
  if (!keyFn) return [...items];
  const sign = dir === "asc" ? 1 : -1;
  return items
    .map((f, i) => ({ f, i, k: keyFn(f) }))
    .sort((x, y) => {
      for (let n = 0; n < x.k.length; n++) {
        const a = x.k[n], b = y.k[n];
        if (a == null && b == null) continue;
        if (a == null) return 1; // null zawsze na koncu
        if (b == null) return -1;
        const c = cmp(a, b);
        if (c !== 0) return sign * c;
      }
      return x.i - y.i; // stabilnosc
    })
    .map((e) => e.f);
}
