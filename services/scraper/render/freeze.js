// Zamrozony snapshot strony do korpusu offline (fixtures/demo-ads/facebook/<id>/page.html).
//
// Dlaczego nie HAR: aplikacja Meta przy kazdym ladowaniu wysyla zapytania
// GraphQL z tokenami/znacznikami czasu, ktore nie pasuja do nagrania — przy
// odtwarzaniu HAR dialog z reklama w ogole sie nie renderuje (sprawdzone na
// zywo 21.11.2026). Zamiast odtwarzac aplikacje, zamrazamy JEJ WYNIK:
//   * klon wyrenderowanego DOM (zywy dokument zostaje nietkniety),
//   * zewnetrzne arkusze CSS wklejone jako <style>,
//   * obrazy z zakresu jako data: URI,
//   * wszystkie skrypty usuniete OPROCZ type="application/json" (wezel reklamy).
//
// stage "collect": { css: [href...], imgs: [src...] } do pobrania przez Pythona.
// stage "build":   { css: {href: tekst}, imgs: {src: dataUri} } -> HTML (string).
(opts) => {
  const keep = opts.keepSelector ? document.querySelector(opts.keepSelector) : null;
  const imgScope = keep || document.body;

  if (opts.stage === "collect") {
    const css = [...document.querySelectorAll('link[rel~="stylesheet"][href]')].map((l) => l.href);
    const imgs = [...new Set([...imgScope.querySelectorAll("img[src]")]
      .map((i) => i.src).filter((s) => /^https?:/.test(s)))];
    return { css, imgs };
  }

  const cssMap = opts.css || {};
  const imgMap = opts.imgs || {};
  const liveImgs = [...document.querySelectorAll("img")];
  const clone = document.documentElement.cloneNode(true);
  const cloneImgs = [...clone.querySelectorAll("img")];

  // obrazy: dopasowanie po pozycji (klon ma te same elementy w tej samej kolejnosci)
  cloneImgs.forEach((img, i) => {
    const live = liveImgs[i];
    img.removeAttribute("srcset");
    img.removeAttribute("loading");
    if (live && imgMap[live.src]) img.setAttribute("src", imgMap[live.src]);
  });

  for (const s of clone.querySelectorAll("script")) {
    const isJson = (s.getAttribute("type") || "").toLowerCase() === "application/json";
    // JSON zostaje tylko, gdy niesie wezel nagrywanej reklamy (reszta to megabajty balastu)
    if (!isJson || (opts.keepJsonContaining && !s.textContent.includes(opts.keepJsonContaining))) s.remove();
  }
  for (const l of clone.querySelectorAll('link[rel~="preload"],link[rel~="modulepreload"],link[rel~="prefetch"],link[rel~="preconnect"],link[rel~="dns-prefetch"]')) {
    l.remove();
  }
  const liveLinks = [...document.querySelectorAll('link[rel~="stylesheet"][href]')];
  [...clone.querySelectorAll('link[rel~="stylesheet"][href]')].forEach((l, i) => {
    const href = liveLinks[i] ? liveLinks[i].href : null;
    if (href && cssMap[href] != null) {
      const style = document.createElement("style");
      style.setAttribute("data-frozen-from", href);
      style.textContent = cssMap[href];
      l.replaceWith(style);
    } else {
      l.remove();
    }
  });
  const meta = document.createElement("meta");
  meta.setAttribute("name", "investwatch-frozen-at");
  meta.setAttribute("content", new Date().toISOString());
  const head = clone.querySelector("head");
  if (head) head.prepend(meta);
  return "<!doctype html>\n" + clone.outerHTML;
}
