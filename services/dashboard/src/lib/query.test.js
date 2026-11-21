import { test } from "node:test";
import assert from "node:assert/strict";
import { applyFilters, stats, trend, isReviewed } from "./query.js";

const items = [
  { id: "a", risk_level: "high", risk_score: 80, status: "new", modules: [1, 2], created_at: "2026-11-20T10:00:00Z", document: { source: "facebook", title: "Forex" } },
  { id: "b", risk_level: "low", risk_score: 10, status: "confirmed", modules: [3], created_at: "2026-11-21T10:00:00Z", document: { source: "youtube", title: "ETF" } },
];

test("filtry listowe, data, prog i weryfikacja", () => {
  assert.deepEqual(applyFilters(items, { source: ["facebook"] }).map((f) => f.id), ["a"]);
  assert.deepEqual(applyFilters(items, { module: ["3"] }).map((f) => f.id), ["b"]);
  assert.deepEqual(applyFilters(items, { from: "2026-11-21T00:00:00Z" }).map((f) => f.id), ["b"]);
  assert.deepEqual(applyFilters(items, { min_score: 50, reviewed: "false" }).map((f) => f.id), ["a"]);
  assert.equal(isReviewed(items[1]), true);
});

test("agregaty", () => {
  assert.equal(stats(items).by_source.facebook, 1);
  assert.deepEqual(trend(items).map((d) => d.date), ["2026-11-20", "2026-11-21"]);
});
