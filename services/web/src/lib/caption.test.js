import { test } from "node:test";
import assert from "node:assert/strict";
import { adRef, cleanQuote, isPolish, keyQuote, twinIndex } from "./caption.js";

test("cleanQuote: bez adresow, znakow laczacych i ucietego slowa", () => {
  assert.equal(cleanQuote("o appears twice, including one big gain"), "appears twice, including one big gain");
  assert.equal(cleanQuote("͞ ͞ ͞ ͞ Earn 40% a month now"), "Earn 40% a month now");
  assert.equal(cleanQuote("d/pl/plans/2?period=12 https://x.example.invalid/a"), "");
  assert.ok(cleanQuote("A".repeat(10) + " " + "słowo ".repeat(60)).endsWith("…"));
});

test("keyQuote: najpierw dowod najciezszej reguly, potem tytul", () => {
  const f = { document: { title: "Program Partnerski mBanku" }, rule_results: [
    { verdict: "fail", severity: 3, evidence: { quote: "Zarobiłem ponad 55 tys zł na programie" } },
    { verdict: "fail", severity: 5, evidence: { quote: "https://example.invalid" } },
  ] };
  assert.equal(keyQuote(f), "Zarobiłem ponad 55 tys zł na programie");
  assert.equal(keyQuote({ document: { title: "Program Partnerski mBanku" }, rule_results: [] }), "Program Partnerski mBanku");
});

test("jezyk, numer reklamy, zdublowana kreacja", () => {
  assert.equal(isPolish("Zarobiłem ponad 55 tys"), true);
  assert.equal(cleanQuote("Gwarantowany zysk, żadnego ryzyka"), "Gwarantowany zysk, żadnego ryzyka"); // ogonki zostaja
  assert.equal(isPolish("How to buy stocks at XTB"), false);
  assert.deepEqual(adRef({ url: "https://example.invalid/ads/library/?id=1700487841682444" }), { kind: "reklama", id: "1700487841682444" });
  assert.deepEqual(adRef({ url: "https://www.youtube.com/watch?v=QF9vUVdhh18" }), { kind: "film", id: "QF9vUVdhh18" });
  const q = [
    { document: { publisher_display_name: "Squaber", title: "2027 na giełdzie" } },
    { document: { publisher_display_name: "Squaber", title: "2027 na giełdzie " } },
    { document: { publisher_display_name: "Inny", title: "Wilanów" } },
  ];
  assert.equal(twinIndex(q, 0), 1);
  assert.equal(twinIndex(q, 2), -1);
});
