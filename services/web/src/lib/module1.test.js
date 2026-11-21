import { test } from "node:test";
import assert from "node:assert/strict";
import { flagLabel, buildQuery, csvUrl, clip, screenshotInfo, summarize, safeHref } from "./module1.js";

test("etykiety flag", () => {
  assert.equal(flagLabel("firma_zagraniczna"), "firma zagraniczna");
  assert.equal(flagLabel("nieznana"), "nieznana");
});

test("query pomija puste", () => {
  assert.equal(buildQuery({ source: "x", relation: "", flag: undefined, limit: 50 }), "source=x&limit=50");
});

test("csvUrl bez paginacji", () => {
  assert.equal(csvUrl({ relation: "third_party", limit: 200 }), "/api/reports/module1.csv?relation=third_party");
  assert.equal(csvUrl({}), "/api/reports/module1.csv");
});

test("clip i zrzut", () => {
  assert.equal(clip("a".repeat(200)).length, 141);
  assert.deepEqual(screenshotInfo("s3://shots/a.png"), { href: null, name: "a.png" });
  assert.equal(screenshotInfo("https://h.example.invalid/a.png").href, "https://h.example.invalid/a.png");
  assert.equal(screenshotInfo(null), null);
});

test("safeHref", () => {
  assert.equal(safeHref("http://a.example.invalid/x"), "http://a.example.invalid/x");
  assert.equal(safeHref("https://a.example.invalid"), "https://a.example.invalid");
  assert.equal(safeHref("javascript:alert(1)"), null);
  assert.equal(safeHref("data:text/html,x"), null);
  assert.equal(safeHref(""), null);
  assert.equal(safeHref(null), null);
  assert.equal(safeHref("/relative"), null);
});

test("kafelki", () => {
  const s = summarize(
    [
      { relation: "third_party", m1_flags: ["podmiot_trzeci_bez_ujawnienia", "firma_zagraniczna"] },
      { relation: "official", m1_flags: [] },
    ],
    2,
  );
  assert.deepEqual(s, { total: 2, thirdParty: 1, noDisclosure: 1, foreign: 1 });
});
