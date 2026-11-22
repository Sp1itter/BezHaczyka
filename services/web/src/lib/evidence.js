// Dowod reguly -> struktura do wyswietlenia (bez JSX, testowalna).
const isHttp = (u) => typeof u === "string" && /^https?:\/\//i.test(u);

export const safeHttpUrl = (u) => (isHttp(u) ? u : null);

export const fmtTs = (sec) => {
  const s = Math.max(0, Math.floor(Number(sec)));
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
};

const fmtValue = (k, v) => {
  if (typeof v === "number" && /ratio/i.test(k)) return v.toFixed(2); // stosunki: 2 miejsca
  if (v && typeof v === "object") return JSON.stringify(v);
  return String(v);
};

const fmtViewport = (vp) => {
  if (!vp) return null;
  if (typeof vp === "string") return `okno ${vp}`;
  const w = vp.width ?? vp.w, h = vp.height ?? vp.h;
  return w == null || h == null ? null : `okno ${w}×${h} px`;
};

export function formatEvidence(ev) {
  if (!ev) return { quote: null, summary: null, measured: [], timestamp: null, viewport: null, screenshot: null };
  return {
    quote: ev.quote ? `„${ev.quote}”` : null,
    summary: ev.summary || null,
    measured: Object.entries(ev.measured || {}).map(([key, v]) => ({ key, value: fmtValue(key, v) })),
    timestamp: ev.transcript_ts == null ? null : fmtTs(ev.transcript_ts),
    viewport: fmtViewport(ev.viewport),
    screenshot: safeHttpUrl(ev.screenshot_crop),
  };
}
