// Kategoria naruszenia dla reguly (karta "Najczesciej lamane reguly"; liczniki daje GET /stats).

// Kategorie wg podzialu 18 kryteriow UKNF (art. 44 rozp. del. 2017/565) i Modulu 3.
const CATEGORY = [
  [/^(1|2)$/, "Identyfikacja i oznaczenie reklamy"],
  [/^(3|4|5|6|7|8)$/, "Informacja o ryzyku"],
  [/^(9|10|11)$/, "Rzetelność i zrozumiałość"],
  [/^(12a|12b|13|14)$/, "Wyniki historyczne"],
  [/^15$/, "Prognozy"],
  [/^16$/, "Informacja podatkowa"],
  [/^(17|18)$/, "Odwołania do nadzoru"],
  [/^M3$/, "Działalność bez zezwolenia"],
];
export const categoryOf = (id) => (CATEGORY.find(([re]) => re.test(String(id))) || [null, "Inne"])[1];
