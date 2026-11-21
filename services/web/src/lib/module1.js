// Czyste funkcje raportu Modulu 1: etykiety flag i budowa query stringu.
export const FLAGS = {
  podmiot_trzeci_bez_ujawnienia: "podmiot trzeci bez ujawnienia",
  link_afiliacyjny_bez_ujawnienia: "link afiliacyjny bez ujawnienia",
  cofniete_zezwolenie: "cofnięte zezwolenie",
  firma_zagraniczna: "firma zagraniczna",
  zakonczona_dzialalnosc: "zakończona działalność",
};

export const flagLabel = (f) => FLAGS[f] || f;

/** Query string z niepustych filtrow. */
export function buildQuery(filters = {}) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v === "" || v === null || v === undefined) continue;
    p.append(k, v);
  }
  return p.toString();
}

export const csvUrl = (filters) => {
  const q = buildQuery({ ...filters, limit: "", offset: "" });
  return "/api/reports/module1.csv" + (q ? `?${q}` : "");
};

export const clip = (s, n = 140) => {
  const t = s || "";
  return t.length > n ? t.slice(0, n).trimEnd() + "…" : t;
};

/** Bezpieczny href: tylko http(s), inaczej null (ochrona przed javascript:/data:). */
export const safeHref = (u) => (typeof u === "string" && /^https?:\/\//i.test(u) ? u : null);

/** Zrzut: http(s) -> href, inaczej sama nazwa pliku. */
export function screenshotInfo(uri) {
  if (!uri) return null;
  return { href: safeHref(uri), name: uri.split("/").pop() };
}

export function summarize(items = [], total = 0) {
  const has = (r, f) => (r.m1_flags || []).includes(f);
  return {
    total,
    thirdParty: items.filter((r) => r.relation === "third_party").length,
    noDisclosure: items.filter(
      (r) => has(r, "podmiot_trzeci_bez_ujawnienia") || has(r, "link_afiliacyjny_bez_ujawnienia"),
    ).length,
    foreign: items.filter((r) => has(r, "firma_zagraniczna")).length,
  };
}
