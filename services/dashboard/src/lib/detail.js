// Etykiety i grupowanie dla raportu pozycji (bez JSX, testowalne).
export const VERDICT = { fail: "naruszenie", pass: "OK", not_applicable: "n/d", uncertain: "niepewne" };
export const ENGINE = {
  LLM: "model językowy (Bielik)",
  DET: "pomiar renderu",
  HYBRID: "hybryda: pomiar + tekst",
};
export const RELATION = { official: "oficjalny", third_party: "podmiot trzeci", unknown: "nieznana" };

// Grupy: numeryczne id (w tym 12a/12b) = modul 2, M3 = modul 3, reszta = inne.
export const groupOf = (id) => (/^\d+[a-z]?$/i.test(String(id)) ? "m2" : id === "M3" ? "m3" : "other");
export const GROUPS = [
  ["m2", "Moduł 2 — informacja o ryzyku"],
  ["m3", "Moduł 3 — doradztwo bez zezwolenia"],
  ["other", "Inne"],
];
