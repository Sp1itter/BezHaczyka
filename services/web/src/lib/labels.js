export const MODULES = {
  1: "Moduł 1 — finfluencerzy / podmioty trzecie",
  2: "Moduł 2 — informacja o ryzyku",
  3: "Moduł 3 — usługi nieautoryzowane",
};

export const RISK = { high: "wysokie", medium: "średnie", low: "niskie" };

export const STATUS = {
  new: "nowy",
  triage: "triage",
  in_review: "w weryfikacji",
  confirmed: "potwierdzony",
  dismissed: "odrzucony",
};

export const VERDICT = {
  fail: "naruszenie",
  pass: "zgodne",
  not_applicable: "nie oceniono",
  uncertain: "do weryfikacji",
};

export const RELATION = {
  official: "oficjalny kanał firmy",
  third_party: "podmiot trzeci",
  unknown: "nieustalona",
};

export const pct = (x) => (x === null || x === undefined ? "—" : `${Math.round(x * 100)}%`);
export const fmtDate = (s) => (s ? new Date(s).toLocaleString("pl-PL") : "—");

// --- Slownik panelu bez zargonu (plan, par. 9) ---
export const MODULE_SHORT = { 1: "Podmioty trzecie", 2: "Informacja o ryzyku", 3: "Doradztwo bez zezwolenia" };
export const SOURCE = { facebook: "Facebook", instagram: "Instagram", youtube: "YouTube", www: "WWW", www_live: "WWW",
  tiktok: "TikTok", tiktok_ads: "TikTok (reklamy)" };
export const SCOPE = { in_scope: "w zakresie", out_of_scope: "poza zakresem", uncertain: "zakres niepewny" };
export const ENGINE = { DET: "pomiar z renderu", LLM: "ocena modelu", HYBRID: "pomiar i ocena modelu" };
export const sourceLabel = (s) => SOURCE[s] || s || "—";
export const fmtDay = (s) => (s ? new Date(s).toLocaleDateString("pl-PL") : "—");
export const fmtShort = (s) =>
  s ? new Date(s).toLocaleString("pl-PL", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—";

/** Tytuly ze scrapera bywaja pelne emoji; w tabeli i naglowkach je wyciszamy. */
export const quiet = (s) =>
  String(s || "").replace(/\p{Extended_Pictographic}|️|‍/gu, "").replace(/\s{2,}/g, " ").trim();

/** Publikujacy z AdDocument.publisher (obiekt) albo tekst. */
export const publisherName = (doc) => {
  const p = doc?.publisher;
  if (!p) return "";
  if (typeof p === "string") return p;
  return p.display_name || p.handle || p.name || "";
};
