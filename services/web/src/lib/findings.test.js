import { test } from "node:test";
import assert from "node:assert/strict";
import { apiFilters, csvCell, groupRules, pageParams, toCsv } from "./findings.js";
import { href, pageOf, parseHash } from "./router.js";
import { quiet } from "./labels.js";

test("filtry z adresu -> parametry API (daty wlacznie, puste pomijane)", () => {
  const f = apiFilters({ from: "2026-11-20", to: "2026-11-21", risk: "high", q: "" });
  assert.equal(f.from, "2026-11-20T00:00:00Z");
  assert.equal(f.to, "2026-11-21T23:59:59Z");
  assert.equal(f.risk_level, "high");
  assert.equal(f.q, undefined);
});

test("stronicowanie po stronie serwera", () => {
  assert.deepEqual(pageParams({ page: "2", size: "25" }), { pageIndex: 2, pageSize: 25, limit: 25, offset: 50 });
  assert.equal(pageParams({ size: "7" }).pageSize, 50);
});

test("naruszenia na gorze szuflady, nieocenione osobno", () => {
  const g = groupRules([
    { rule_id: "2", verdict: "fail", severity: 3 },
    { rule_id: "3", verdict: "fail", severity: 5 },
    { rule_id: "4", verdict: "not_applicable" },
    { rule_id: "9", verdict: "pass" },
  ]);
  assert.deepEqual(g.failed.map((r) => r.rule_id), ["3", "2"]);
  assert.equal(g.notAssessed.length, 1);
  assert.equal(g.passed.length, 1);
});

test("CSV: separator srednik, cudzyslowy, ochrona przed formula", () => {
  assert.equal(csvCell('a"b'), '"a""b"');
  assert.equal(csvCell("=HYPERLINK(1)"), "'=HYPERLINK(1)");
  assert.equal(toCsv([{ t: "x;y" }], [{ label: "Tytuł", value: (r) => r.t }]), 'Tytuł\r\n"x;y"');
});

test("router i wyciszanie emoji", () => {
  assert.deepEqual(parseHash("#/wyniki?risk=high"), { path: "/wyniki", query: { risk: "high" } });
  assert.equal(href("/wyniki", { q: "", page: 0 }), "#/wyniki?page=0");
  assert.equal(pageOf("/"), "wyniki");
  assert.equal(pageOf("/nic"), "notfound");
  assert.equal(quiet("Inwestuj mądrze 📈🏗️"), "Inwestuj mądrze");
});
