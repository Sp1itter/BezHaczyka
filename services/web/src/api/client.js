// Jedyny klient HTTP panelu. Komponenty nie wolaja fetch bezposrednio.
// Filtrowanie, stronicowanie i agregaty liczy services/api (panel nie pobiera calej bazy).
// Dev: proxy Vite /api -> API_URL; Docker: nginx /api -> api:8000.
import { buildQuery, csvUrl } from "../lib/module1.js";

const BASE = "/api";
export const PAGE_SIZE = 50;

async function http(path, opts = {}) {
  const res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...opts });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    // detail: tekst albo lista bledow walidacji (422) - pokazujemy je czytelnie, w linii
    const detail = typeof body.detail === "string" ? body.detail
      : Array.isArray(body.detail) ? body.detail.map((d) => d.msg || String(d)).join("; ") : null;
    throw Object.assign(new Error(detail || `Błąd API (HTTP ${res.status})`), { status: res.status, body });
  }
  return body;
}

/** Parametry zapytania; tablice jako powtorzone klucze (status=new&status=triage). */
export function toQuery(params = {}) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === "" || v === null || v === undefined) continue;
    (Array.isArray(v) ? v : [v]).forEach((x) => p.append(k, x));
  }
  return p.toString();
}

const patch = (id, body) => http(`/findings/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(body) });

export const api = {
  // Lista: lekki tryb (bez pelnych wynikow regul), stronicowanie po stronie serwera.
  findings: (params = {}) => http(`/findings?${toQuery({ fields: "list", limit: PAGE_SIZE, ...params })}`),
  finding: (id) => http(`/findings/${encodeURIComponent(id)}`),
  events: (id) => http(`/findings/${encodeURIComponent(id)}/events`),
  review: (id, label, note, actor) => patch(id, { review: { label, note: note || null }, actor }),
  assign: (id, assignee, actor) => patch(id, { assignee, actor }),
  setStatus: (id, status, actor) => patch(id, { status, actor }),
  reviewLabels: () => http(`/review-labels`),
  stats: (params = {}) => http(`/stats?${toQuery(params)}`),
  trend: (params = {}) => http(`/stats/trend?${toQuery({ bucket: "auto", ...params })}`),
  calibration: () => http(`/calibration`),
  threshold: () => http(`/settings/threshold`),
  saveThreshold: (value, actor) => http(`/settings/threshold`, { method: "PUT", body: JSON.stringify({ value, actor }) }),
  health: () => http(`/health`),
  document: (id) => http(`/documents/${encodeURIComponent(id)}`),
  // Uzupelnia brakujace kadry filmow YouTube w magazynie (idempotentne; wylaczone = enabled:false).
  backfillFrames: () => http(`/documents/frames/backfill`, { method: "POST" }),
  module1Report: (filters = {}) => http(`/reports/module1?${buildQuery({ ...filters, limit: 500 })}`),
  module1CsvUrl: (filters = {}) => csvUrl(filters, BASE),
  module3Report: (filters = {}) => http(`/reports/module3?${toQuery({ limit: 500, ...filters })}`),
  module3CsvUrl: (filters = {}) => `${BASE}/reports/module3.csv?${toQuery(filters)}`,
  scaling: () => http(`/ops/scaling`),
  saveScaling: (body) => http(`/ops/scaling`, { method: "PUT", body: JSON.stringify(body) }),
};

export const screenshotUrl = (documentId, viewport = "mobile") =>
  `${BASE}/documents/${encodeURIComponent(documentId)}/screenshot?viewport=${viewport}`;
