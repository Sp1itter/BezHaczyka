// Napisy do kadru wideo i rozpoznanie zdublowanych kreacji w kolejce (bez JSX, testowalne).

const MAX = 160;

/** Czysci fragment dowodu: bez adresow, znakow laczacych i ucietych slow na brzegach okna. */
export function cleanQuote(raw, max = MAX) {
  let s = String(raw || "")
    .normalize("NFC").replace(/[̀-ͯ]/g, "") // osierocone znaki laczace; polskie litery zostaja (NFC)
    .replace(/https?:\/\/\S+|www\.\S+|\S*[/=&]\S*/gi, " ") // adresy i ich resztki z okna dowodu
    .replace(/[^\p{L}\p{N}\s.,!?%:;'"()\-–+€$zł]/gu, " ")
    .replace(/\s+/g, " ").trim();
  if (!s) return "";
  const words = s.split(" ");
  // okno dowodu zaczyna sie zwykle w polowie slowa: odrzuc pierwszy token, jesli nie zaczyna zdania
  if (words.length > 3 && /^\p{Ll}/u.test(words[0])) words.shift();
  s = words.join(" ");
  if (s.length > max) s = s.slice(0, max).replace(/\s+\S*$/, "") + "…";
  return s.length >= 12 ? s : "";
}

/** Kluczowy cytat: fragment, ktory zlapala najwazniejsza zlamana regula; inaczej tytul. */
export function keyQuote(finding) {
  const failed = (finding.rule_results || []).filter((r) => r.verdict === "fail")
    .sort((a, b) => (b.severity ?? 0) - (a.severity ?? 0));
  for (const r of failed) {
    const q = cleanQuote(r.evidence?.quote);
    if (q) return q;
  }
  return cleanQuote(finding.document?.title) || "";
}

const PL = /[ąćęłńóśźż]|\b(i|w|się|nie|jest|na|że|oraz|dla)\b/i;
export const isPolish = (text) => PL.test(text || "");

/** Numer reklamy z adresu Biblioteki reklam (?id=...) albo identyfikator filmu YouTube (?v=...). */
export function adRef(doc) {
  const m = /[?&](id|v)=([\w-]+)/.exec(doc?.url || "");
  return m ? { kind: m[1] === "v" ? "film" : "reklama", id: m[2] } : null;
}

/** Inna pozycja kolejki z ta sama kreacja (ten sam nadawca i tytul) - indeks od 0 albo -1. */
export function twinIndex(queue, index) {
  const key = (f) => `${f.document?.publisher_display_name || ""}|${(f.document?.title || "").trim().toLowerCase()}`;
  const k = key(queue[index] || {});
  if (!queue[index]?.document?.title) return -1;
  return queue.findIndex((f, i) => i !== index && key(f) === k);
}
