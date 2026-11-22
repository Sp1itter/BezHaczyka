// Etykiety i grupowanie dla raportu pozycji (bez JSX, testowalne).
export const VERDICT = { fail: "naruszenie", pass: "zgodna", not_applicable: "nie dotyczy", uncertain: "nieoceniona" };
export const RELATION = { official: "oficjalny", third_party: "podmiot trzeci", unknown: "nieznana" };

// Grupy: numeryczne id (w tym 12a/12b) = modul 2, M3 = modul 3, reszta = inne.
export const groupOf = (id) => (/^\d+[a-z]?$/i.test(String(id)) ? "m2" : id === "M3" ? "m3" : "other");
export const GROUPS = [
  ["m2", "Moduł 2 — treść reklamy (art. 44)"],
  ["m3", "Moduł 3 — doradztwo bez zezwolenia"],
  ["other", "Inne"],
];
