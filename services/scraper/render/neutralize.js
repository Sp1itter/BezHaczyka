// Neutralizacja nakladek logowania / zgody na cookies — BEZ KLIKANIA (par. 6.2.1).
//
// Wywolanie: page.evaluate(NEUTRALIZE_JS, { keepSelector })
// Usuwa z DOM nakladki (role=dialog, aria-modal, <dialog open>, elementy
// position:fixed zaslaniajace ekran), ktore:
//   * NIE zawieraja elementu keepSelector i nie sa w nim zawarte,
//   * pasuja do sygnatury logowania albo cookies.
// Przywraca przewijanie (Meta blokuje overflow na html/body pod modalem).
// Zwraca liste rodzajow usunietych nakladek — trafia do logu jako dowod audytowy.
(opts) => {
  const keep = opts && opts.keepSelector ? document.querySelector(opts.keepSelector) : null;
  const LOGIN_RE = /(zaloguj|log in|login|zarejestruj|sign up|create new account|utw[oó]rz nowe konto)/i;
  const COOKIE_RE = /(cookie|plik[oó]w? cookie|ciasteczk)/i;

  const kindOf = (el) => {
    if (el.querySelector("[data-cookiebanner]") || el.hasAttribute("data-cookiebanner")) return "cookie";
    if (el.querySelector('input[type=password],input[name=email],input[name=pass],form[action*="login"]')) return "login";
    const head = (el.innerText || "").slice(0, 600);
    if (COOKIE_RE.test(head)) return "cookie";
    if (LOGIN_RE.test(head)) return "login";
    return null;
  };
  const related = (el) => keep && (el === keep || el.contains(keep) || keep.contains(el));

  const candidates = new Set(
    document.querySelectorAll('[role=dialog],[aria-modal=true],dialog[open],[data-cookiebanner]')
  );
  for (const el of document.querySelectorAll("body *")) {
    const cs = getComputedStyle(el);
    if (cs.position !== "fixed") continue;
    const r = el.getBoundingClientRect();
    if (r.width * r.height > 0.3 * innerWidth * innerHeight || r.height >= 0.15 * innerHeight) candidates.add(el);
  }

  const removed = [];
  for (const el of candidates) {
    if (!el.isConnected || related(el)) continue;
    const kind = kindOf(el);
    if (!kind) continue;
    el.remove();
    removed.push(kind);
  }
  for (const el of [document.documentElement, document.body]) {
    if (!el) continue;
    el.style.setProperty("overflow", "visible", "important");
    el.style.setProperty("position", "static", "important");
  }
  return removed;
}
