// Jedyny klient HTTP panelu. Komponenty nie wolaja fetch bezposrednio.
// PUNKT POLACZENIA: BASE. Dev -> proxy Vite (vite.config.js), Docker -> nginx /api -> API_UPSTREAM
// (services/api :8000 albo mock :4000). Korzysta tylko z endpointow, ktore ma services/api.
import { applyFilters, stats, trend } from "../lib/query.js";
import { buildQuery, csvUrl } from "../lib/module1.js";

const BASE = import.meta.env.VITE_API_BASE || "/api";
const LIMIT = 500; // maksimum GET /findings w services/api

async function http(path, opts = {}) {
  const res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

// Krotki cache listy, zeby kilka widokow naraz nie pytalo API wielokrotnie.
let cache = { at: 0, promise: null };
function allFindings() {
  if (!cache.promise || Date.now() - cache.at > 2000) {
    cache = { at: Date.now(), promise: http(`/findings?limit=${LIMIT}`).then((r) => r.items || []) };
    cache.promise.catch(() => (cache = { at: 0, promise: null }));
  }
  return cache.promise;
}
const invalidate = () => (cache = { at: 0, promise: null });

const patch = (id, body) =>
  http(`/findings/${id}`, { method: "PATCH", body: JSON.stringify(body) }).finally(invalidate);

export const api = {
  // [DB-1] lista + filtry (filtry liczone lokalnie)
  findings: async (filters) => {
    const items = applyFilters(await allFindings(), filters);
    return { items, total: items.length };
  },
  finding: (id) => http(`/findings/${id}`), // [DB-2]
  updateFinding: (id, body) => patch(id, body), // [DB-3]
  // [DB-3] Ocena czlowieka z etykieta feedbacku (TP/FP/...); status wynika z etykiety po stronie API.
  review: (id, label, note, actor) => patch(id, { review: { label, note: note || null }, actor }),
  // [DB-3] Przypisanie / przejecie alertu; null zwalnia.
  assign: (id, assignee, actor) => patch(id, { assignee, actor }),
  events: (id) => http(`/findings/${id}/events`), // [DB-8] historia pracy (finding_events)
  reviewLabels: () => http(`/review-labels`), // [DB-9] slownik etykiet feedbacku
  stats: async (filters) => stats(applyFilters(await allFindings(), filters)), // [DB-4]
  trend: async (filters) => ({ items: trend(applyFilters(await allFindings(), filters)) }), // [DB-5]
  calibration: () => http(`/calibration`), // [DB-6]
  // Raport Modulu 1 (503, gdy widok bazy niedostepny) i link do CSV z tymi samymi filtrami.
  module1Report: (filters = {}) => http(`/reports/module1?${buildQuery({ ...filters, limit: 500 })}`),
  module1CsvUrl: (filters = {}) => csvUrl(filters, BASE),
};
