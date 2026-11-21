import { test } from "node:test";
import assert from "node:assert/strict";
import { VERDICT, ENGINE, RELATION, groupOf, GROUPS } from "./detail.js";

test("etykiety obejmuja wszystkie wartosci enumow", () => {
  for (const v of ["pass", "fail", "not_applicable", "uncertain"]) assert.ok(VERDICT[v], v);
  for (const e of ["LLM", "DET", "HYBRID"]) assert.ok(ENGINE[e], e);
  for (const r of ["official", "third_party", "unknown"]) assert.ok(RELATION[r], r);
});

test("groupOf", () => {
  assert.equal(groupOf("1"), "m2");
  assert.equal(groupOf("12a"), "m2");
  assert.equal(groupOf("M3"), "m3");
  assert.equal(groupOf("X"), "other");
  assert.deepEqual(GROUPS.map((g) => g[0]), ["m2", "m3", "other"]);
});
