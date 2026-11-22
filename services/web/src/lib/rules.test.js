import { test } from "node:test";
import assert from "node:assert/strict";
import { categoryOf } from "./rules.js";

test("kategorie wg podzialu 18 regul UKNF i Modulu 3", () => {
  assert.equal(categoryOf("3"), "Informacja o ryzyku");
  assert.equal(categoryOf("12a"), "Wyniki historyczne");
  assert.equal(categoryOf("M3"), "Działalność bez zezwolenia");
  assert.equal(categoryOf("99"), "Inne");
});
