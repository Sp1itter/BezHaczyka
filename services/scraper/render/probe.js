// RenderProbe — geometria renderu dla regul DET (design doc par. 6.2 i 6.2.1).
//
// Wywolanie: page.evaluate(PROBE_JS, { scopeSelector, maxNodes })
// Zwraca ViewportProbe: { dominant_font_px, page_height_px, nodes[] } albo null,
// gdy scopeSelector nie trafil w zaden element.
//
// Rozszerzenia wzgledem par. 6.2.1:
//  * scopeSelector (scope_root) — sondujemy TYLKO poddrzewo wskazanego elementu,
//    a sygnaly ukrycia (modal/hidden/accordion/details/link) liczymy tylko miedzy
//    wezlem a korzeniem zakresu. Meta Ad Library pokazuje reklame z `?id=`
//    WEWNATRZ role="dialog" — bez tego kazdy wezel dostalby
//    behind_interaction="modal" i regula 7 oblalaby kazda reklame.
//  * krok 3b — media pod tekstem: `<img>/<video>/<canvas>` NIE sa
//    background-image, wiec algorytm przodkow ich nie widzi. Sprawdzamy stos
//    elementow w punktach bbox (document.elementsFromPoint): jesli pod tekstem
//    lezy medium, zanim trafimy na nieprzezroczyste tlo -> confidence "unknown".
//  * sygnal "link" tylko dla linku TEKSTOWEGO. Blok CTA reklamy (anchor z
//    obrazem w srodku) to widoczna tresc, nie odeslanie „dalej".
(opts) => {
  const scopeSelector = (opts && opts.scopeSelector) || null;
  const maxNodes = (opts && opts.maxNodes) || 400;

  const root = scopeSelector ? document.querySelector(scopeSelector) : document.body;
  if (!root) return null;

  const MEDIA_TAGS = new Set(["IMG", "VIDEO", "CANVAS", "PICTURE", "IMAGE", "IFRAME"]);
  const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE", "TITLE", "SVG"]);

  // ---------------------------------------------------------------- kolory --
  const parseColor = (str) => {
    const m = /rgba?\(([^)]+)\)/.exec(str || "");
    if (!m) return null;
    const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const over = (top, bottom) => {
    // kompozycja alfa: top nad (nieprzezroczystym) bottom
    const a = top.a + bottom.a * (1 - top.a);
    if (a <= 0) return { r: 0, g: 0, b: 0, a: 0 };
    const ch = (c) => (top[c] * top.a + bottom[c] * bottom.a * (1 - top.a)) / a;
    return { r: ch("r"), g: ch("g"), b: ch("b"), a };
  };
  const hex = (c) =>
    "#" + [c.r, c.g, c.b].map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, "0")).join("");
  const lum = (c) => {
    const f = (v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const contrast = (a, b) => {
    const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x);
    return Math.round(((l1 + 0.05) / (l2 + 0.05)) * 100) / 100;
  };

  // --------------------------------------------------------------- sciezki --
  const shortPath = (el, stopAt) => {
    const parts = [];
    let cur = el;
    while (cur && cur.nodeType === 1 && parts.length < 8) {
      let seg = cur.tagName.toLowerCase();
      const parent = cur.parentElement;
      if (parent) {
        const same = Array.from(parent.children).filter((c) => c.tagName === cur.tagName);
        if (same.length > 1) seg += `:nth-of-type(${same.indexOf(cur) + 1})`;
      }
      parts.unshift(seg);
      if (cur === stopAt) break;
      cur = parent;
    }
    return parts.join(">");
  };

  // -------------------------------------------------------- tlo efektywne --
  const backgroundOf = (el) => {
    const layers = [];
    let cur = el;
    let source = null;
    while (cur && cur.nodeType === 1) {
      const cs = getComputedStyle(cur);
      const bf = cs.backdropFilter || cs.webkitBackdropFilter || "none";
      if ((cs.backgroundImage && cs.backgroundImage !== "none") || (bf && bf !== "none")) {
        return { color: null, source: "ancestor:" + shortPath(cur), confidence: "unknown" };
      }
      const c = parseColor(cs.backgroundColor);
      if (c && c.a > 0) {
        layers.push(c);
        if (!source) source = "ancestor:" + shortPath(cur);
        if (c.a >= 1) {
          let result = c;
          for (let i = layers.length - 2; i >= 0; i--) result = over(layers[i], result);
          return { color: result, source, confidence: "resolved" };
        }
      }
      cur = cur.parentElement;
    }
    let result = { r: 255, g: 255, b: 255, a: 1 }; // kanwa
    for (let i = layers.length - 1; i >= 0; i--) result = over(layers[i], result);
    return { color: result, source: source || "canvas", confidence: "assumed_canvas" };
  };

  // krok 3b: czy pod tekstem lezy medium (zanim trafimy na pelne tlo)?
  // Zwraca "media:<tag>", null (sprawdzone, brak mediow) albo undefined
  // (zaden punkt nie byl w viewporcie — trzeba przewinac i sprawdzic ponownie).
  const mediaBeneath = (el, rect) => {
    const pts = [
      [0.5, 0.5], [0.15, 0.25], [0.85, 0.25], [0.15, 0.75], [0.85, 0.75],
    ];
    let checked = false;
    for (const [fx, fy] of pts) {
      const x = rect.left + rect.width * fx;
      const y = rect.top + rect.height * fy;
      if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
      checked = true;
      const stack = document.elementsFromPoint(x, y);
      // Elementy z pointer-events:none (czesty przypadek napisow na grafice)
      // nie pojawiaja sie w stosie — wtedy caly stos lezy POD tekstem.
      let idx = stack.findIndex((s) => s === el || el.contains(s));
      const below = idx >= 0 ? stack.slice(idx + 1) : stack;
      for (const s of below) {
        if (s.contains(el)) {
          // przodek: liczy sie tylko, gdy ma nieprzezroczyste tlo (zaslania reszte)
          const c = parseColor(getComputedStyle(s).backgroundColor);
          if (c && c.a >= 1) break;
          continue;
        }
        if (MEDIA_TAGS.has(s.tagName.toUpperCase())) return "media:" + s.tagName.toLowerCase();
        const cs = getComputedStyle(s);
        if (cs.backgroundImage && cs.backgroundImage !== "none") return "media:background-image";
        const c = parseColor(cs.backgroundColor);
        if (c && c.a >= 1) break;
      }
    }
    return checked ? null : undefined;
  };
  const deferred = []; // [indeks w nodes, element] — media sprawdzane po przewinieciu

  // ---------------------------------------------- zwiniecie / interakcja --
  const controlledCollapsed = (anc) => {
    if (!anc.id) return false;
    try {
      return !!document.querySelector(`[aria-controls~="${CSS.escape(anc.id)}"][aria-expanded="false"]`);
    } catch (e) {
      return false;
    }
  };
  const isTextLink = (a, el) => {
    if (!a.getAttribute("href") || /^(#|javascript:)/i.test(a.getAttribute("href"))) return false;
    if (a.querySelector("img,video,picture,canvas,svg image")) return false; // blok CTA z grafika
    const aLen = (a.innerText || "").trim().length;
    const elLen = (el.innerText || el.textContent || "").trim().length;
    return aLen > 0 && aLen <= Math.max(elLen * 2, 80);
  };
  const interactionOf = (el) => {
    let cur = el;
    while (cur && cur.nodeType === 1) {
      const cs = getComputedStyle(cur);
      const tag = cur.tagName;
      if (tag === "DETAILS" && !cur.open && !(el.closest("summary") && el.closest("details") === cur)) {
        return ["details", "details[not(@open)]"];
      }
      if (cs.display === "none") return ["hidden", "display:none"];
      if (cs.visibility === "hidden") return ["hidden", "visibility:hidden"];
      if (parseFloat(cs.opacity) === 0) return ["hidden", "opacity:0"];
      if (cur.hasAttribute("hidden")) return ["hidden", "[hidden]"];
      if (cur.getAttribute("aria-hidden") === "true") return ["hidden", "aria-hidden=true"];
      const cp = cs.clipPath || "";
      if (/inset\(\s*100%/.test(cp) || /rect\(\s*0(px)?[\s,]+0(px)?[\s,]+0(px)?[\s,]+0(px)?\s*\)/.test(cs.clip || "")) {
        return ["hidden", "clip"];
      }
      const ovh = cs.overflow === "hidden" || cs.overflowY === "hidden" || cs.overflow === "clip" || cs.overflowY === "clip";
      if (ovh && (parseFloat(cs.height) === 0 || cs.maxHeight === "0px")) return ["accordion", "height:0+overflow:hidden"];
      if (cur.getAttribute("aria-expanded") === "false" && cur !== el && !cur.matches("button,[role=button]")) {
        return ["accordion", "aria-expanded=false"];
      }
      if (controlledCollapsed(cur)) return ["accordion", "aria-controls+aria-expanded=false"];
      if (tag === "A" && isTextLink(cur, el)) return ["link", "a[href]"];
      if (tag === "DIALOG" && !cur.open) return ["modal", "dialog[not(@open)]"];
      if (cur.getAttribute("role") === "dialog" || cur.getAttribute("aria-modal") === "true") {
        return ["modal", "role=dialog"];
      }
      if (cur === root) break; // scope_root: wyzej nie patrzymy
      cur = cur.parentElement;
    }
    return [null, null];
  };

  const clippedOf = (el, rect) => {
    if (rect.right > innerWidth + 1 || rect.left < -1) return true; // wyjezdza poza viewport (RWD)
    const cs = getComputedStyle(el);
    if (cs.textOverflow === "ellipsis" && el.scrollWidth > el.clientWidth + 1) return true;
    if (cs.webkitLineClamp && cs.webkitLineClamp !== "none" && el.scrollHeight > el.clientHeight + 1) return true;
    let cur = el.parentElement;
    while (cur && cur.nodeType === 1 && cur !== document.documentElement) {
      const c = getComputedStyle(cur);
      if (/(hidden|clip)/.test(c.overflow + c.overflowX + c.overflowY)) {
        const r = cur.getBoundingClientRect();
        if (r.width > 0 && r.height > 0 &&
            (rect.left < r.left - 1 || rect.right > r.right + 1 || rect.top < r.top - 1 || rect.bottom > r.bottom + 1)) {
          return true;
        }
      }
      cur = cur.parentElement;
    }
    return false;
  };

  // ------------------------------------------------ zbieranie wezlow tekstu --
  const textByElement = new Map();
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => {
      if (!n.nodeValue || !n.nodeValue.replace(/[\s\u200b-\u200f\u2060\ufeff]+/g, "")) return NodeFilter.FILTER_REJECT;
      const p = n.parentElement;
      if (!p || SKIP_TAGS.has(p.tagName.toUpperCase()) || p.closest("svg")) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const p = n.parentElement;
    if (!textByElement.has(p)) textByElement.set(p, []);
    textByElement.get(p).push(n);
  }

  const nodes = [];
  const fontChars = new Map();
  for (const [el, textNodes] of textByElement) {
    if (nodes.length >= maxNodes) break;
    const text = textNodes.map((t) => t.nodeValue).join(" ")
      .replace(/[\u200b-\u200f\u2060\ufeff]/g, "").replace(/\s+/g, " ").trim();
    if (!text) continue;

    let rect = null;
    for (const t of textNodes) {
      const range = document.createRange();
      range.selectNodeContents(t);
      const r = range.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      rect = rect
        ? {
            left: Math.min(rect.left, r.left), top: Math.min(rect.top, r.top),
            right: Math.max(rect.right, r.right), bottom: Math.max(rect.bottom, r.bottom),
          }
        : { left: r.left, top: r.top, right: r.right, bottom: r.bottom };
    }
    if (!rect) {
      const r = el.getBoundingClientRect();
      rect = { left: r.left, top: r.top, right: r.right, bottom: r.bottom };
    }
    rect.width = rect.right - rect.left;
    rect.height = rect.bottom - rect.top;

    const cs = getComputedStyle(el);
    const fontPx = parseFloat(cs.fontSize) || 0;
    const [behind, evidence] = interactionOf(el);
    // Zwiniety wezel NIE jest widoczny, nawet gdy ma bbox: Chromium zostawia
    // pudelko ukladu tresci zamknietego <details> (content-visibility), wiec
    // sama geometria dawala visible=true i R5 mierzyla kontrast niewidocznego tekstu.
    const collapsed = behind === "hidden" || behind === "details" || behind === "accordion"
      || evidence === "dialog[not(@open)]";
    const visible = !collapsed && rect.width > 0 && rect.height > 0;

    let bg = backgroundOf(el);
    if (visible && bg.confidence !== "unknown") {
      const media = mediaBeneath(el, rect);
      if (media) bg = { color: null, source: media, confidence: "unknown" };
      else if (media === undefined) deferred.push([nodes.length, el]);
    }
    let fg = parseColor(cs.color) || { r: 0, g: 0, b: 0, a: 1 };
    if (bg.color && fg.a < 1) fg = over(fg, bg.color);

    nodes.push({
      text: text.slice(0, 2000),
      font_px: Math.round(fontPx * 100) / 100,
      font_weight: parseInt(cs.fontWeight, 10) || 400,
      color: hex(fg),
      background_effective: bg.color ? hex(bg.color) : null,
      background_source: bg.source,
      background_confidence: bg.confidence,
      contrast_ratio: bg.color ? contrast(fg, bg.color) : null,
      bbox: {
        x: Math.round((rect.left + scrollX) * 10) / 10,
        y: Math.round((rect.top + scrollY) * 10) / 10,
        w: Math.round(rect.width * 10) / 10,
        h: Math.round(rect.height * 10) / 10,
      },
      visible,
      clipped: visible ? clippedOf(el, rect) : false,
      behind_interaction: behind,
      collapsed_evidence: evidence,
      dom_path: shortPath(el, root),
      in_footer: !!el.closest("footer,[role=contentinfo]"),
    });
    if (visible) fontChars.set(fontPx, (fontChars.get(fontPx) || 0) + text.length);
  }

  // Drugi przebieg kroku 3b: wezly poza viewportem. Przewijanie zmienia
  // wspolrzedne, dlatego robimy je PO zebraniu bbox wszystkich wezlow.
  if (deferred.length) {
    const [sx, sy] = [scrollX, scrollY];
    for (const [i, el] of deferred) {
      el.scrollIntoView({ block: "center", inline: "nearest" });
      const r = el.getBoundingClientRect();
      const media = mediaBeneath(el, r);
      if (media) {
        Object.assign(nodes[i], {
          background_effective: null, background_source: media,
          background_confidence: "unknown", contrast_ratio: null,
        });
      }
    }
    scrollTo(sx, sy);
  }

  let dominant = 16;
  let best = -1;
  for (const [px, chars] of fontChars) {
    if (chars > best) {
      best = chars;
      dominant = px;
    }
  }

  return {
    dominant_font_px: dominant,
    page_height_px: Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0),
    nodes,
  };
}
