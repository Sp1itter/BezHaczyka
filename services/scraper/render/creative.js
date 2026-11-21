// Oznacza kreacje reklamy w dialogu Meta Ad Library atrybutem data-iw-creative="1".
//
// Wywolanie: page.wait_for_function(MARK_CREATIVE_JS, arg=ad_archive_id) — zwraca
// true, gdy kreacja zostala znaleziona i oznaczona (idempotentnie).
//
// Ustalone na zywo (21.11.2026): `data-testid="ad-library-dynamic-content-container"`
// wystepuje TYLKO w reklamach DCO. Zwykle reklamy (obraz, wideo, karuzela) w dialogu
// go nie maja — ten sam testid jest wtedy wylacznie w kartach listy POD dialogiem.
// Dlatego:
//   1. dialog = role="dialog", ktorego tekst zawiera ad_archive_id,
//   2. jesli w dialogu jest kontener DCO -> to on,
//   3. inaczej: od etykiety „Sponsorowane"/„Sponsored" w gore, do NAJWYZSZEGO przodka,
//      ktory nie zawiera jeszcze metadanych biblioteki (tekstu z ad_archive_id).
//      To jest dokladnie blok kreacji: nazwa strony, tresc, media, CTA.
(adId) => {
  if (document.querySelector('[data-iw-creative="1"]')) return true;
  const dialog = [...document.querySelectorAll('[role="dialog"]')]
    .find((d) => (d.textContent || "").includes(adId));
  if (!dialog) return false;

  let creative = dialog.querySelector('[data-testid="ad-library-dynamic-content-container"]');
  if (!creative) {
    const walker = document.createTreeWalker(dialog, NodeFilter.SHOW_TEXT);
    let label = null;
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (/^\s*(Sponsorowane|Sponsored)\s*$/i.test(n.nodeValue || "")) {
        label = n.parentElement;
        break;
      }
    }
    if (!label) return false;
    let cur = label;
    while (cur.parentElement && cur.parentElement !== dialog &&
           !(cur.parentElement.textContent || "").includes(adId)) {
      cur = cur.parentElement;
    }
    // Kreacja musi miec wiecej niz sama etykiete (nazwa strony + tresc/media).
    if ((cur.innerText || "").trim().length < 20 && !cur.querySelector("img,video")) return false;
    creative = cur;
  }
  creative.setAttribute("data-iw-creative", "1");
  return true;
}
