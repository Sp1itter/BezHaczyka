export const RISK = { high: "Wysokie", medium: "Średnie", low: "Niskie" };
export const RISK_COLOR = { high: "#e7664c", medium: "#d6bf57", low: "#54b399" };
export const STATUS = {
  new: "Nowe",
  triage: "Triage",
  in_review: "W analizie",
  confirmed: "Potwierdzone",
  dismissed: "Odrzucone",
};
export const SOURCE = { youtube: "YouTube", facebook: "Facebook", instagram: "Instagram", www: "WWW" };
export const sourceLabel = (s) => SOURCE[s] || s || "—";

// document.publisher w services/api to obiekt {handle, display_name, profile_url, ...}, w mocku tekst.
export const publisherName = (doc) => {
  const p = doc?.publisher;
  if (!p) return "";
  if (typeof p === "string") return p;
  return p.display_name || p.handle || p.name || "";
};
export const MODULE = { 1: "M1 · Podmioty", 2: "M2 · Treść", 3: "M3 · Rejestr KNF" };
export const ASSIGNED_BY = { ai: "AI", human: "człowiek" };
export const DECISION = { confirmed: "Potwierdzone", dismissed: "Odrzucone" };
// Statusy koncowe: tylko decyzja czlowieka w weryfikacji.
export const HUMAN_ONLY = ["confirmed", "dismissed"];
export const ANALYSTS = ["analityk.a", "analityk.b", "analityk.c"];

export const fmtDate = (iso) =>
  new Date(iso).toLocaleString("pl-PL", { dateStyle: "short", timeStyle: "short" });
