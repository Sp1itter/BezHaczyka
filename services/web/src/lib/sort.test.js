import { test } from "node:test";
import assert from "node:assert/strict";
import { sortFindings } from "./sort.js";

const items = [
  { id: "a", risk_level: "medium", risk_score: 50, created_at: "2026-11-20T10:00:00Z", status: "new", primary_module: 2, document: { source: "www", publisher: { display_name: "Zeta" } } },
  { id: "b", risk_level: "high", risk_score: 70, created_at: "2026-11-21T10:00:00Z", status: "triage", primary_module: 1, document: { source: "facebook", publisher: null } },
  { id: "c", risk_level: "high", risk_score: 90, created_at: null, status: "new", primary_module: null, document: { source: "youtube", publisher: "Ala" } },
  { id: "d", risk_level: "low", risk_score: 50, created_at: "2026-11-19T10:00:00Z", status: "new", primary_module: 2, document: { source: "www" } },
];
const ids = (r) => r.map((f) => f.id).join("");

test("ryzyko: poziom, potem wynik; kierunki", () => {
  assert.equal(ids(sortFindings(items, "risk", "desc")), "cbad");
  assert.equal(ids(sortFindings(items, "risk", "asc")), "dabc");
});

test("null na koncu w obu kierunkach", () => {
  assert.equal(ids(sortFindings(items, "date", "desc")), "badc");
  assert.equal(ids(sortFindings(items, "date", "asc")), "dabc");
  assert.equal(sortFindings(items, "module", "desc").at(-1).id, "c");
  assert.equal(sortFindings(items, "module", "asc").at(-1).id, "c");
  assert.equal(ids(sortFindings(items, "publisher", "asc")), "cabd");
});

test("stabilnosc i brak mutacji", () => {
  const copy = [...items];
  assert.equal(ids(sortFindings(items, "status", "asc")), "acdb");
  assert.deepEqual(items, copy);
  assert.equal(ids(sortFindings(items, "score", "desc")), "cbad");
  assert.equal(ids(sortFindings(items, "source", "asc")), "badc");
});
