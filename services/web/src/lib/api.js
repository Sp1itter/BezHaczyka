// Klient API. Wszystkie sciezki przez /api (proxy vite w dev, nginx w compose).
import { buildQuery } from "./module1.js";
const BASE = "/api";

async function call(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`${options.method || "GET"} ${path}: HTTP ${res.status}`);
  return res.json();
}

export function listFindings(filters) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v === "" || v === null || v === undefined) continue;
    (Array.isArray(v) ? v : [v]).forEach((x) => p.append(k, x));
  }
  return call(`/findings?${p}`);
}

export async function getModule1Report(filters) {
  const q = buildQuery({ ...filters, limit: filters.limit ?? 200 });
  const res = await fetch(`${BASE}/reports/module1?${q}`);
  if (!res.ok) {
    throw new Error(
      res.status === 503
        ? "Raport Modułu 1 jest chwilowo niedostępny (brak widoku w bazie — uruchom migracje casedb)."
        : `Nie udało się pobrać raportu (HTTP ${res.status}).`,
    );
  }
  return res.json();
}

export const getFinding =(id) => call(`/findings/${id}`);
export const getStats = () => call("/stats");
export const getCalibration = () => call("/calibration");
export const getHealth = () => call("/health");
export const setStatus = (id, status) =>
  call(`/findings/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });

/** WebSocket alertow z automatycznym ponowieniem polaczenia. Zwraca funkcje zamykajaca. */
export function subscribeAlerts(onMessage, onState) {
  let ws;
  let closed = false;
  let retry;
  const open = () => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/ws/alerts`);
    ws.onopen = () => onState(true);
    ws.onmessage = (e) => {
      try {
        onMessage(JSON.parse(e.data));
      } catch {
        /* zly komunikat pomijamy */
      }
    };
    ws.onclose = () => {
      onState(false);
      if (!closed) retry = setTimeout(open, 3000);
    };
  };
  open();
  return () => {
    closed = true;
    clearTimeout(retry);
    ws?.close();
  };
}
