// Jedyny klient HTTP panelu. Komponenty nie wolaja fetch bezposrednio.
// PUNKT POLACZENIA: BASE. Dev -> proxy Vite (vite.config.js), Docker -> nginx /api -> services/api.
const BASE = import.meta.env.VITE_API_BASE || "/api";

async function http(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

// Filtry panelu -> query string w formacie services/api (listy jako powtorzone klucze).
export function toQuery(filters = {}) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v == null || v === "") continue;
    if (Array.isArray(v)) v.forEach((x) => sp.append(k, x));
    else sp.set(k, v);
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  findings: (filters) => http(`/findings${toQuery({ limit: 500, ...filters })}`), // [DB-1]
  finding: (id) => http(`/findings/${id}`), // [DB-2]
  updateFinding: (id, patch) => http(`/findings/${id}`, { method: "PATCH", body: JSON.stringify(patch) }), // [DB-3]
  stats: (filters) => http(`/stats${toQuery(filters)}`), // [DB-4]
  trend: (filters) => http(`/stats/trend${toQuery(filters)}`), // [DB-5]
  calibration: () => http(`/calibration`), // [DB-6]
};
