// Powloka panelu: port base.html + logiki menu z app.js wzorca PRAKTYKI (bez znakow instytucjonalnych wzorca).
import { useEffect, useRef, useState } from "react";
import { BRAND, NAV_GROUPS } from "../config.js";

// Domyslnie pasek ikon rozsuwany po najechaniu; przycisk [|<] (albo Ctrl+B) przypina pelne menu.
const STORAGE_KEY = "bezhaczyka-sidebar-pinned";
const DESKTOP = "(min-width: 861px)";
const CLOSE_DELAY_MS = 150; // bez migotania przy szybkim przejsciu kursora przez krawedz

function storedPinned() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) !== "false"; // domyslnie menu z podpisami
  } catch {
    return true; // brak localStorage nie blokuje nawigacji
  }
}

function savePinned(value) {
  try {
    window.localStorage.setItem(STORAGE_KEY, String(value));
  } catch {
    /* brak localStorage nie blokuje nawigacji */
  }
}

function MenuIcon() {
  return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M4 4h16v16H4zM9 4v16M15 9l-3 3 3 3" /></svg>;
}

export default function Shell({ active, counts, health, live, analyst, analysts, onAnalyst, children }) {
  const [desktop, setDesktop] = useState(() => window.matchMedia(DESKTOP).matches);
  const [pinned, setPinned] = useState(storedPinned);
  const [hover, setHover] = useState(false);
  const closeTimer = useRef(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const sidebarRef = useRef(null);
  const mobileButtonRef = useRef(null);

  useEffect(() => {
    const mq = window.matchMedia(DESKTOP);
    const onChange = () => { setDesktop(mq.matches); setMobileOpen(false); };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const toggle = () => {
    if (desktop) {
      setPinned((v) => { savePinned(!v); return !v; });
      setHover(false);
    } else {
      setMobileOpen((o) => !o);
    }
  };

  useEffect(() => {
    const onKey = (e) => {
      const t = e.target;
      const editing = t instanceof HTMLElement && (t.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(t.tagName));
      if (desktop && !editing && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
        e.preventDefault();
        toggle();
      }
      if (!desktop && e.key === "Escape" && mobileOpen) {
        setMobileOpen(false);
        mobileButtonRef.current?.focus();
      }
    };
    const onClick = (e) => {
      if (!desktop && mobileOpen && sidebarRef.current && !sidebarRef.current.contains(e.target)
        && !e.target.closest("[data-menu-toggle]")) setMobileOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("click", onClick);
    return () => { document.removeEventListener("keydown", onKey); document.removeEventListener("click", onClick); };
  });

  const overlay = desktop && !pinned; // pasek ikon w ukladzie, pelne menu wysuwa sie nad trescia
  const isCollapsed = overlay && !hover;
  const expanded = desktop ? !isCollapsed : mobileOpen;
  const menuTitle = desktop ? `${pinned ? "Odepnij" : "Przypnij"} menu (Ctrl+B)` : `${mobileOpen ? "Zamknij" : "Otwórz"} menu`;
  const openHover = () => { window.clearTimeout(closeTimer.current); if (overlay) setHover(true); };
  const closeHover = () => { window.clearTimeout(closeTimer.current); closeTimer.current = window.setTimeout(() => setHover(false), CLOSE_DELAY_MS); };
  const apiOk = health?.status === "ok";

  return (
    <div className={`app-shell ${isCollapsed ? "sidebar-collapsed" : ""} ${overlay ? "sidebar-overlay" : ""}`}>
      <a className="skip-link" href="#content" onClick={(e) => { e.preventDefault(); document.getElementById("content")?.focus(); }}>
        Przejdź do treści
      </a>
      <aside className={`sidebar ${mobileOpen ? "open" : ""}`} id="sidebar" ref={sidebarRef}
        onMouseEnter={openHover} onMouseLeave={closeHover} onFocus={openHover}
        onBlur={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) closeHover(); }}>
        <div className="brand">
          <button className="menu-button sidebar-menu-button" type="button" data-menu-toggle aria-controls="sidebar"
            aria-expanded={expanded} aria-keyshortcuts="Control+B" title={menuTitle} onClick={toggle}>
            <MenuIcon />
            <span className="sr-only">Pokaż lub ukryj menu</span>
          </button>
          <span className="brand-copy">
            <strong>{BRAND.name}</strong>
            <small>{BRAND.subtitle}</small>
          </span>
        </div>
        <nav className="main-nav" aria-label="Nawigacja główna">
          {NAV_GROUPS.map((g) => (
            <section className="nav-group" key={g.id} aria-labelledby={`nav-${g.id}`}>
              <h2 className="nav-group-label" id={`nav-${g.id}`}>{g.label}</h2>
              {g.items.map((it) => {
                const count = counts[it.id];
                const isActive = active === it.id;
                return (
                  <a key={it.id} href={it.href} title={it.label} data-tooltip={it.label}
                    className={`nav-item ${isActive ? "active" : ""}`} aria-current={isActive ? "page" : undefined}
                    onClick={() => !desktop && setMobileOpen(false)}>
                    <span className="nav-icon" aria-hidden="true">
                      <svg viewBox="0 0 24 24">{it.icon.map((d) => <path key={d} d={d} />)}</svg>
                    </span>
                    <span className="nav-label">{it.label}</span>
                    {count ? <span className="nav-count" aria-label={`${count} oczekujących`}>{count < 100 ? count : "99+"}</span> : null}
                  </a>
                );
              })}
            </section>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="system-line" title={apiOk ? "Usługa dostępna" : "API niedostępne"}>
            <span className={`status-dot ${apiOk ? "" : "down"}`} />
            <span className="system-label">{apiOk ? "System działa" : health ? "Brak połączenia z systemem" : "Sprawdzam połączenie…"}</span>
          </div>
          <label className="analyst-picker" title="Wybierz analityka">
            <span className="analyst-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM4 21a8 8 0 0 1 16 0" /></svg>
            </span>
            <span className="analyst-copy">
              <small>Analityk</small>
              <strong>{analyst}</strong>
            </span>
            <span className="analyst-chevron" aria-hidden="true" />
            <select aria-label="Wybierz analityka" value={analyst} onChange={(e) => onAnalyst(e.target.value)}>
              {analysts.map((a) => <option key={a}>{a}</option>)}
            </select>
          </label>
        </div>
      </aside>

      <section className="workspace">
        <header className="command-bar">
          <div className="command-start">
            <button className="menu-button mobile-menu-button" type="button" data-menu-toggle aria-controls="sidebar"
              aria-expanded={mobileOpen} title={menuTitle} onClick={toggle} ref={mobileButtonRef}>
              <MenuIcon />
              <span className="sr-only">Pokaż lub ukryj menu</span>
            </button>

          </div>
          <div className="command-session">
            <span className={`live-state ${live ? "on" : ""}`} title="Alerty wysokiego ryzyka przychodzą na bieżąco">
              <span className="status-dot" />{live ? "Alerty na żywo" : "Łączenie ponownie…"}
            </span>
          </div>
        </header>
        <main id="content" className="content" tabIndex={-1}>
          {children}
        </main>
      </section>
    </div>
  );
}
