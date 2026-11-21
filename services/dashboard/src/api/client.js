// Jedyny klient HTTP panelu. Komponenty nie wolaja fetch bezposrednio.
// PUNKT POLACZENIA: BASE. Dev -> proxy Vite (vite.config.js), Docker -> nginx /api -> API_UPSTREAM
// (services/api :8000 albo mock :4000). Korzysta tylko z endpointow, ktore ma services/api.
import { applyFilters, stats, trend } from "../lib/query.js";

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
  // [DB-3] Decyzja czlowieka. services/api zapisuje dzis tylko `status`;
  // `review` i `actor` (kto, kiedy, notatka) czekaja na kolumny reviewed_by/reviewed_at/review_note.
  review: (id, decision, note, actor) => patch(id, { status: decision, review: { decision, note }, actor }),
  // [DB-3] Przypisanie. services/api nie ma jeszcze kolumn assignee/assigned_by (mock je ma).
  // services/api wymaga pola status w PATCH, wiec odsylamy biezacy.
  assign: async (id, assignee, actor) => {
    const f = await http(`/findings/${id}`);
    return patch(id, { status: f.status, assignee, actor });
  },
  stats: async (filters) => stats(applyFilters(await allFindings(), filters)), // [DB-4]
  trend: async (filters) => ({ items: trend(applyFilters(await allFindings(), filters)) }), // [DB-5]
  calibration: () => http(`/calibration`), // [DB-6]
};
