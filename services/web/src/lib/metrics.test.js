import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { confusion, scores, sweep, bestF1, coverage, effectiveFails } from "./metrics.js";

const items = [
  { score: 80, is_violation: true },
  { score: 60, is_violation: false },
  { score: 30, is_violation: true },
  { score: 10, is_violation: false },
  { score: null, is_violation: true },
];

test("confusion przy progu 50", () => {
  assert.deepEqual(confusion(items, 50), { tp: 1, fp: 1, fn: 1, tn: 1, skipped: 1 });
});

test("precision/recall/F1", () => {
  const s = scores({ tp: 1, fp: 1, fn: 1, tn: 1 });
  assert.equal(s.precision, 0.5);
  assert.equal(s.recall, 0.5);
  assert.equal(s.f1, 0.5);
  assert.equal(scores({ tp: 0, fp: 0, fn: 2, tn: 2 }).precision, null);
});

test("sweep i najlepszy F1", () => {
  const rows = sweep(items);
  assert.equal(rows.length, 101);
  const best = bestF1(rows);
  assert.ok(best.f1 >= 0.66 && best.threshold <= 30);
});

test("coverage i progi pewnosci", () => {
  const rr = [
    { verdict: "fail", confidence: 0.9 },
    { verdict: "fail", confidence: 0.4 },
    { verdict: "pass", confidence: 1 },
    { verdict: "not_applicable", confidence: 1 },
  ];
  assert.equal(coverage(rr), 0.75);
  const e = effectiveFails(rr, 0.5);
  assert.equal(e.fails.length, 1);
  assert.equal(e.uncertain.length, 1);
});

test("zgodnosc z evaluate.py: przy progu 50 na zbiorze zlotym TP=0 FP=0 FN=3 TN=5", () => {
  const gold = JSON.parse(readFileSync(new URL("../../../../fixtures/gold/labels.json", import.meta.url)));
  assert.deepEqual(confusion(gold.items, 50), { tp: 0, fp: 0, fn: 3, tn: 5, skipped: 0 });
});
