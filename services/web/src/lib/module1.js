// Czyste funkcje raportu Modulu 1: etykiety, budowa query, bezpieczne linki.
export const FLAGS = {
  podmiot_trzeci_bez_ujawnienia: "podmiot trzeci bez ujawnienia",
  link_afiliacyjny_bez_ujawnienia: "link afiliacyjny bez ujawnienia",
  cofniete_zezwolenie: "cofnięte zezwolenie",
  zakonczona_dzialalnosc: "zakończona działalność",
  firma_zagraniczna: "firma zagraniczna",
};
export const RELATIONS = { official: "oficjalna", third_party: "podmiot trzeci", unknown: "nieznana" };

export const flagLabel = (f) => FLAGS[f] || f;
export const relationLabel = (r) => RELATIONS[r] || r || "—";

/** Query string z niepustych filtrow. */
export function buildQuery(filters = {}) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v === "" || v === null || v === undefined) continue;
    p.append(k, v);
  }
  return p.toString();
}

/** Link do CSV: te same filtry, bez paginacji. */
export function csvUrl(filters = {}, base = "/api") {
  const q = buildQuery({ ...filters, limit: "", offset: "" });
  return `${base}/reports/module1.csv${q ? `?${q}` : ""}`;
}

export const clip = (s, n = 140) => {
  const t = s || "";
  return t.length > n ? t.slice(0, n).trimEnd() + "…" : t;
};

/** Bezpieczny href: tylko http(s) (ochrona przed javascript:/data:). */
export const safeHref = (u) => (typeof u === "string" && /^https?:\/\//i.test(u) ? u : null);

export function summarize(items = [], total = 0) {
  const has = (r, f) => (r.m1_flags || []).includes(f);
  return {
    total,
    thirdParty: items.filter((r) => r.relation === "third_party").length,
    noDisclosure: items.filter((r) => has(r, "podmiot_trzeci_bez_ujawnienia") || has(r, "link_afiliacyjny_bez_ujawnienia")).length,
    foreign: items.filter((r) => has(r, "firma_zagraniczna")).length,
  };
}
