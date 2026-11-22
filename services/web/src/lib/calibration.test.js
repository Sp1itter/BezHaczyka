import { test } from "node:test";
import assert from "node:assert/strict";
import { confusion } from "./calibration.js";

const items = [
  { score: 90, is_violation: true },
  { score: 70, is_violation: false },
  { score: 40, is_violation: true },
  { score: 10, is_violation: false },
];

test("wyzszy prog: mniej FP, wiecej FN", () => {
  const lo = confusion(items, 30);
  const hi = confusion(items, 80);
  assert.deepEqual([lo.tp, lo.fp, lo.fn, lo.tn], [2, 1, 0, 1]);
  assert.deepEqual([hi.tp, hi.fp, hi.fn, hi.tn], [1, 0, 1, 2]);
  assert.ok(hi.precision > lo.precision && hi.recall < lo.recall);
});
