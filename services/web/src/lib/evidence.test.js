import { test } from "node:test";
import assert from "node:assert/strict";
import { formatEvidence, fmtTs, safeHttpUrl } from "./evidence.js";

test("pelny dowod", () => {
  const e = formatEvidence({
    summary: "Mala czcionka", quote: "zysk gwarantowany",
    measured: { font_px: 9.5, contrast_ratio: 2.5, label: "x" },
    viewport: { width: 390, height: 844 }, transcript_ts: 75,
    screenshot_crop: "https://x.example.invalid/a.png",
  });
  assert.equal(e.quote, "„zysk gwarantowany”");
  assert.deepEqual(e.measured, [
    { key: "font_px", value: "9.5" }, { key: "contrast_ratio", value: "2.50" }, { key: "label", value: "x" },
  ]);
  assert.equal(e.timestamp, "01:15");
  assert.equal(e.viewport, "okno 390×844 px");
  assert.equal(e.screenshot, "https://x.example.invalid/a.png");
});

test("braki i niebezpieczne linki", () => {
  const e = formatEvidence({ summary: "s", measured: null, screenshot_crop: "javascript:alert(1)" });
  assert.equal(e.screenshot, null);
  assert.equal(e.timestamp, null);
  assert.deepEqual(e.measured, []);
  assert.equal(formatEvidence(null).quote, null);
  assert.equal(fmtTs(0), "00:00");
  assert.equal(safeHttpUrl("ftp://x"), null);
});
