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

/** Parametry zapytania; tablice jako powtorzone klucze (risk_level=high&risk_level=low). */
export function toQuery(filters = {}) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v === "" || v === null || v === undefined) continue;
    (Array.isArray(v) ? v : [v]).forEach((x) => p.append(k, x));
  }
  return p.toString();
}

export const listFindings = (filters) => call(`/findings?${toQuery(filters)}`);
export const getTrend = (filters) => call(`/stats/trend?${toQuery({ ...filters, bucket: "day" })}`);
export const getEvents = (id) => call(`/findings/${id}/events`);
export const getReviewLabels = () => call("/review-labels");
export const reviewFinding = (id, label, note, actor) =>
  call(`/findings/${id}`, { method: "PATCH", body: JSON.stringify({ review: { label, note: note || null }, actor }) });
export const assignFinding = (id, assignee, actor) =>
  call(`/findings/${id}`, { method: "PATCH", body: JSON.stringify({ assignee, actor }) });
/** Zrzut reklamy przez API (proxy S3); 404/503 obsluguje <img onError>. */
export const screenshotUrl = (documentId, viewport = "mobile") =>
  `${BASE}/documents/${encodeURIComponent(documentId)}/screenshot?viewport=${viewport}`;

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

export const getFinding = (id) => call(`/findings/${id}`);
export const getStats = (filters = {}) => call(`/stats?${toQuery(filters)}`);
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

/** Raport Modulu 3 (doradztwo bez zezwolenia), GET /reports/module3. */
export async function getModule3Report(filters = {}) {
  const res = await fetch(`${BASE}/reports/module3?${toQuery({ limit: 500, ...filters })}`);
  if (!res.ok) {
    throw new Error(res.status === 404
      ? "Raport Modułu 3 nie jest jeszcze dostępny w API."
      : `Nie udało się pobrać raportu Modułu 3 (HTTP ${res.status}).`);
  }
  return res.json();
}
export const module3CsvUrl = (filters = {}) => `${BASE}/reports/module3.csv?${toQuery(filters)}`;

/** Panel operatora: proxy API do autoskalera (/ops/scaling). */
export const getScaling = () => call("/ops/scaling");
export async function putScaling(body) {
  const res = await fetch(`${BASE}/ops/scaling`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(json.detail || `HTTP ${res.status}`), { status: res.status });
  return json;
}

/** Prog alertow zapisany po stronie serwera (alerty WS go respektuja). */
export const getThreshold = () => call("/settings/threshold");
export const putThreshold = (value) => call("/settings/threshold", { method: "PUT", body: JSON.stringify({ value }) });
