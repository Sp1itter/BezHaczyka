// Routing na hashu (#/strona?param=...). Adres jest zrodlem prawdy dla strony i filtrow,
// wiec widok z filtrami mozna skopiowac i wyslac.
import { useEffect, useState } from "react";

export function parseHash(hash = window.location.hash) {
  const raw = hash.replace(/^#/, "") || "/";
  const [path, qs = ""] = raw.split("?");
  return { path: path || "/", query: Object.fromEntries(new URLSearchParams(qs)) };
}

export function href(path, query = {}) {
  const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== "" && v != null)).toString();
  return `#${path}${qs ? `?${qs}` : ""}`;
}

export function navigate(path, query = {}, { replace = false } = {}) {
  const next = href(path, query);
  if (window.location.hash === next) return;
  if (replace) {
    window.history.replaceState(null, "", next);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  } else {
    window.location.hash = next;
  }
}

export function useRoute() {
  const [route, setRoute] = useState(() => parseHash());
  useEffect(() => {
    const onChange = () => setRoute(parseHash());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

export const PAGES = ["wyniki", "alerty", "kalibracja", "raporty", "operator"];

export function pageOf(path) {
  const name = path.replace(/^\//, "").split("/")[0] || "wyniki";
  return PAGES.includes(name) ? name : "notfound";
}
