import { test } from "node:test";
import assert from "node:assert/strict";
import { flagLabel, relationLabel, buildQuery, csvUrl, clip, safeHref, summarize } from "./module1.js";

test("etykiety", () => {
  assert.equal(flagLabel("firma_zagraniczna"), "firma zagraniczna");
  assert.equal(flagLabel("x"), "x");
  assert.equal(relationLabel("third_party"), "podmiot trzeci");
});
test("query pomija puste", () => {
  assert.equal(buildQuery({ source: "x", relation: "", flag: undefined, limit: 500 }), "source=x&limit=500");
});
test("csvUrl bez paginacji", () => {
  assert.equal(csvUrl({ relation: "third_party", limit: 500 }), "/api/reports/module1.csv?relation=third_party");
  assert.equal(csvUrl({}), "/api/reports/module1.csv");
});
test("clip", () => {
  assert.equal(clip("a".repeat(200)).length, 141);
  assert.equal(clip(null), "");
});
test("safeHref", () => {
  assert.equal(safeHref("https://a.example.invalid"), "https://a.example.invalid");
  assert.equal(safeHref("javascript:alert(1)"), null);
  assert.equal(safeHref(null), null);
});
test("summarize", () => {
  const items = [
    { relation: "third_party", m1_flags: ["podmiot_trzeci_bez_ujawnienia", "firma_zagraniczna"] },
    { relation: "official", m1_flags: [] },
  ];
  assert.deepEqual(summarize(items, 9), { total: 9, thirdParty: 1, noDisclosure: 1, foreign: 1 });
});
