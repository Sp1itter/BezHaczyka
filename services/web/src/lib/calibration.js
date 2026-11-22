// Kalibracja progu: wynik >= threshold => model mowi "naruszenie".
// FP: model mowi naruszenie, a w zbiorze zlotym go nie ma. FN: odwrotnie.
export function confusion(items, threshold) {
  let tp = 0, fp = 0, fn = 0, tn = 0;
  for (const it of items) {
    const pred = it.score >= threshold;
    if (pred && it.is_violation) tp++;
    else if (pred) fp++;
    else if (it.is_violation) fn++;
    else tn++;
  }
  const precision = tp + fp ? tp / (tp + fp) : 0;
  const recall = tp + fn ? tp / (tp + fn) : 0;
  const f1 = precision + recall ? (2 * precision * recall) / (precision + recall) : 0;
  return { tp, fp, fn, tn, precision, recall, f1 };
}

export function sweep(items, step = 5) {
  const out = [];
  for (let t = 0; t <= 100; t += step) out.push({ threshold: t, ...confusion(items, t) });
  return out;
}
