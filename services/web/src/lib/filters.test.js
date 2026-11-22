import { test } from "node:test";
import assert from "node:assert/strict";
import { isOpen, toApiFilters } from "./filters.js";
import { compareValues, firstDirection, sortRows, statusClass } from "./ui.js";
import { parseHash, href, matchRoute } from "./router.js";

const items = [
  { id: "a", risk_score: 90 }, { id: "b", risk_score: 5 },
];

test("filtry z adresu -> parametry API (zakres dat wlacznie)", () => {
  assert.deepEqual(toApiFilters({ risk: "high", source: "youtube", module: "3", status: "new", q: "xtb", from: "2026-11-20", to: "2026-11-21" }), {
    q: "xtb", risk_level: "high", module: "3", status: "new", source: "youtube",
    from: "2026-11-20T00:00:00Z", to: "2026-11-21T23:59:59Z",
  });
  assert.equal(toApiFilters({}).risk_level, undefined);
  assert.ok(isOpen({ status: "triage" }) && !isOpen({ status: "confirmed" }));
});

test("sortowanie jak sort-button wzorca", () => {
  assert.equal(firstDirection("date"), "desc");
  assert.equal(firstDirection("severity"), "asc");
  assert.ok(compareValues("high", "low", "severity") < 0);
  const col = { type: "number", sortValue: (f) => f.risk_score };
  assert.deepEqual(sortRows(items, col, "asc").map((f) => f.id), ["b", "a"]);
  assert.equal(statusClass("dismissed"), "false_positive");
  assert.equal(statusClass("cokolwiek"), "neutral");
});

test("router na hashu", () => {
  assert.deepEqual(parseHash("#/findings?risk=high"), { path: "/findings", query: { risk: "high" } });
  assert.equal(href("/alerts", { q: "", risk: "high" }), "#/alerts?risk=high");
  assert.deepEqual(matchRoute("/findings/abc"), { name: "finding", id: "abc" });
  assert.equal(matchRoute("/nie-ma").name, "notfound");
  assert.equal(matchRoute("/module3").name, "module3");
  assert.equal(matchRoute("/operator").name, "operator");
});
