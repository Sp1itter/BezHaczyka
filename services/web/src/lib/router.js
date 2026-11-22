// Routing na hashu (#/sciezka?param=...). Odpowiednik miekkiej nawigacji wzorca:
// adres jest zrodlem prawdy dla widoku i filtrow (link do widoku z filtrami da sie skopiowac).
import { useEffect, useState } from "react";

export function parseHash(hash = window.location.hash) {
  const raw = hash.replace(/^#/, "") || "/";
  const [path, qs = ""] = raw.split("?");
  const query = Object.fromEntries(new URLSearchParams(qs));
  return { path: path || "/", query };
}

export function href(path, query = {}) {
  const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== "" && v != null)).toString();
  return `#${path}${qs ? `?${qs}` : ""}`;
}

export function navigate(path, query = {}) {
  const next = href(path, query);
  if (window.location.hash !== next) window.location.hash = next;
}

export function useRoute() {
  const [route, setRoute] = useState(() => parseHash());
  useEffect(() => {
    const onChange = () => {
      setRoute(parseHash());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

// "/findings/abc" -> { name: "finding", id: "abc" }
export function matchRoute(path) {
  const m = path.match(/^\/findings\/([^/]+)$/);
  if (m) return { name: "finding", id: decodeURIComponent(m[1]) };
  const name = { "/": "overview", "/alerts": "alerts", "/findings": "findings", "/module1": "module1", "/module2": "module2",
    "/module3": "module3", "/calibration": "calibration", "/operator": "operator" }[path];
  return { name: name || "notfound" };
}
