// Dane przykladowe w ksztalcie kontraktu Finding (services/api/api/contracts.py)
// + podglad dokumentu (DOC_PREVIEW z services/api/api/store.py).
// Rozklad danych jest staly (ziarno), identyfikatory losowe przy kazdym starcie.
import { randomUUID } from "node:crypto";

let seed = 20261121;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const pick = (arr) => arr[Math.floor(rnd() * arr.length)];
const uuid = () => randomUUID();

export const SOURCES = ["youtube", "facebook", "www"];
export const STATUSES = ["new", "triage", "in_review", "confirmed", "dismissed"];
export const ANALYSTS = ["analityk.a", "analityk.b", "analityk.c"];
// Statusy koncowe ustawia tylko czlowiek przez weryfikacje (review).
export const HUMAN_ONLY = ["confirmed", "dismissed"];

const RULES = [
  { rule_id: "1", rule_name: "Brak oznaczenia reklamy", engine: "LLM", severity: 3 },
  { rule_id: "2", rule_name: "Obietnica zysku bez ostrzezenia", engine: "LLM", severity: 5 },
  { rule_id: "3", rule_name: "Brak ostrzezenia o ryzyku", engine: "DET", severity: 5 },
  { rule_id: "4", rule_name: "Rozmiar czcionki ryzyka", engine: "DET", severity: 4 },
  { rule_id: "5", rule_name: "Ekspozycja i kontrast ryzyka", engine: "DET", severity: 4 },
  { rule_id: "9", rule_name: "Wyniki historyczne bez zastrzezen", engine: "LLM", severity: 4 },
  { rule_id: "18", rule_name: "Nadzor jako argument bezpieczenstwa", engine: "LLM", severity: 5 },
  { rule_id: "22", rule_name: "Podmiot spoza rejestru KNF", engine: "DET", severity: 5 },
];

const TITLES = [
  "Jak zarobic 20% miesiecznie na forexie",
  "Kryptowaluty bez ryzyka - poradnik",
  "Inwestycja w apartamenty, zwrot 9% rocznie",
  "Najlepszy broker 2026 - recenzja",
  "Pasywny dochod z obligacji",
  "Copy trading: kopiuj ekspertow",
  "Fundusz ETF dla poczatkujacych",
  "Sygnaly tradingowe premium",
];
const PUBLISHERS = ["@finfluencer_pl", "Inwestor Pro", "Rynki24", "Kasa Plus", "TraderJoe", "Gielda TV"];
const FIRMS = [
  { name: "XYZ Dom Maklerski", knf_id: "DM-123", authorized: true },
  { name: "QuickFX Ltd", knf_id: null, authorized: false },
  { name: "Alfa TFI", knf_id: "TFI-045", authorized: true },
  { name: "CryptoMax", knf_id: null, authorized: false },
];

const levelFor = (score) => (score >= 65 ? "high" : score >= 35 ? "medium" : "low");

export function makeFinding(createdAt = new Date()) {
  const source = pick(SOURCES);
  const primary_module = 1 + Math.floor(rnd() * 3);
  const modules = [...new Set([primary_module, 1 + Math.floor(rnd() * 3)])].sort();
  const risk_score = Math.round(rnd() * 1000) / 10;
  const firm = pick(FIRMS);
  const publisher = pick(PUBLISHERS);
  const rule_results = RULES.filter(() => rnd() < 0.5).map((r) => {
    const verdict = rnd() < risk_score / 100 ? "fail" : pick(["pass", "not_applicable"]);
    return {
      ...r,
      verdict,
      confidence: Math.round((0.5 + rnd() * 0.5) * 100) / 100,
      legal_basis: "art. 44 rozporzadzenia del. 2017/565",
      evidence: {
        kind: verdict === "fail" ? pick(["quote", "measurement"]) : "absence",
        summary: verdict === "fail" ? `Naruszenie: ${r.rule_name.toLowerCase()}.` : "Brak naruszenia.",
        quote: verdict === "fail" ? "Gwarantowany zysk bez zadnego ryzyka!" : null,
        measured: null,
        viewport: pick(["desktop", "mobile", null]),
        screenshot_crop: null,
        transcript_ts: null,
      },
    };
  });
  const id = uuid();
  return {
    id,
    document_id: uuid(),
    primary_module,
    modules,
    routing: {
      rule: pick(["R1", "R2", "R3", "R4"]),
      reason: `${publisher} reklamuje ${firm.name}${firm.authorized ? "" : " (brak w rejestrze KNF)"}.`,
      scope_gate: "in_scope",
    },
    risk_score,
    risk_level: levelFor(risk_score),
    rule_results,
    entities: {
      investment_firm: {
        name_in_ad: firm.name,
        registry_match: firm.knf_id ? { knf_id: firm.knf_id, official_name: firm.name, score: 0.9 } : null,
        is_authorized: firm.authorized,
      },
      advertiser: { name: publisher, relation_to_firm: pick(["own", "third_party", "unknown"]) },
    },
    knn_score: Math.round(rnd() * 100) / 100,
    status: "new",
    // Sugestia modelu: tylko podpowiedz, decyzje podejmuje czlowiek.
    ai_suggestion: {
      status: risk_score >= 50 ? "confirmed" : "dismissed",
      assignee: pick(ANALYSTS),
      confidence: Math.round((0.55 + rnd() * 0.45) * 100) / 100,
    },
    assignee: null,
    assigned_by: null, // "ai" | "human"
    review: null, // { decision, by, at, note } - wylacznie decyzja czlowieka
    created_at: createdAt.toISOString(),
    document: {
      source,
      url: `https://example.invalid/${source}/${id.slice(0, 8)}`,
      title: pick(TITLES),
      publisher,
      lang: "pl",
    },
  };
}

// Historia: czesc rekordow przypisana (przez AI lub czlowieka), czesc juz zweryfikowana.
function withHistory(f) {
  const r = rnd();
  if (r < 0.35) return f;
  f.assignee = rnd() < 0.5 ? f.ai_suggestion.assignee : pick(ANALYSTS);
  f.assigned_by = f.assignee === f.ai_suggestion.assignee && rnd() < 0.6 ? "ai" : "human";
  if (r < 0.55) f.status = "triage";
  else if (r < 0.7) f.status = "in_review";
  else {
    const decision = rnd() < 0.8 ? f.ai_suggestion.status : f.ai_suggestion.status === "confirmed" ? "dismissed" : "confirmed";
    f.status = decision;
    f.review = { decision, by: f.assignee, at: f.created_at, note: null };
  }
  return f;
}

export function makeFindings(n = 240, days = 45) {
  const now = Date.now();
  return Array.from({ length: n }, () => withHistory(makeFinding(new Date(now - rnd() * days * 86400000))))
    .sort((a, b) => b.created_at.localeCompare(a.created_at));
}

// Zbior zloty do kalibracji (ksztalt GET /calibration z services/api).
export function makeGold(n = 120) {
  return Array.from({ length: n }, (_, i) => {
    const is_violation = rnd() < 0.45;
    const base = is_violation ? 62 : 32;
    const score = Math.max(0, Math.min(100, Math.round((base + (rnd() - 0.5) * 60) * 10) / 10));
    return { id: `gold-${i + 1}`, score, is_violation, coverage: Math.round(rnd() * 100) / 100 };
  });
}
