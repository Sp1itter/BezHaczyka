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
