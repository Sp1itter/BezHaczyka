// Logika panelu kalibracji — liczona W PRZEGLADARCE, bez requestu do modelu.
// Zrodlo prawdy dla etykiet: fixtures/gold/labels.json (serwowane przez GET /calibration).

/** Macierz pomylek dla progu: material jest flagowany, gdy score >= threshold. */
export function confusion(items, threshold) {
  const m = { tp: 0, fp: 0, fn: 0, tn: 0, skipped: 0 };
  for (const it of items) {
    if (typeof it.score !== "number" || typeof it.is_violation !== "boolean") {
      m.skipped += 1; // pozycja bez score'u jest w zbiorze, ale nie w metrykach
      continue;
    }
    const flagged = it.score >= threshold;
    if (flagged && it.is_violation) m.tp += 1;
    else if (flagged) m.fp += 1;
    else if (it.is_violation) m.fn += 1;
    else m.tn += 1;
  }
  return m;
}

const ratio = (a, b) => (b === 0 ? null : a / b);

export function scores(m) {
  const precision = ratio(m.tp, m.tp + m.fp);
  const recall = ratio(m.tp, m.tp + m.fn);
  const f1 =
    precision === null || recall === null || precision + recall === 0
      ? null
      : (2 * precision * recall) / (precision + recall);
  return { precision, recall, f1 };
}

/** Przemiatanie progow 0..100 — dane do wykresu P/R/F1 i FP/FN. */
export function sweep(items, step = 1) {
  const out = [];
  for (let t = 0; t <= 100; t += step) {
    const m = confusion(items, t);
    out.push({ threshold: t, ...m, ...scores(m) });
  }
  return out;
}

export function bestF1(rows) {
  let best = null;
  for (const r of rows) if (r.f1 !== null && (best === null || r.f1 > best.f1)) best = r;
  return best;
}

/** Odsetek regul ocenionych. not_applicable to NIE naruszenie, tylko brak danych. */
export function coverage(ruleResults) {
  if (!ruleResults?.length) return 0;
  return ruleResults.filter((r) => r.verdict !== "not_applicable").length / ruleResults.length;
}

/**
 * Flagi przy progu pewnosci: `fail` liczy sie tylko, gdy confidence >= minConfidence.
 * Nizsza pewnosc => "do weryfikacji", nie naruszenie. Pelne rule_results trzymamy w API
 * wlasnie po to, zeby ten przelicznik byl natychmiastowy.
 */
export function effectiveFails(ruleResults, minConfidence) {
  const fails = [];
  const uncertain = [];
  for (const r of ruleResults || []) {
    if (r.verdict !== "fail") continue;
    (r.confidence >= minConfidence ? fails : uncertain).push(r);
  }
  return { fails, uncertain };
}
