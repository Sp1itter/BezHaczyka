import { useCallback, useEffect, useRef, useState } from "react";
import Shell from "./components/Shell.jsx";
import ErrorBoundary from "./components/common/ErrorBoundary.jsx";
import { PageHeader, ErrorState } from "./components/ui.jsx";
import Overview from "./views/Overview.jsx";
import Alerts from "./views/Alerts.jsx";
import Findings from "./views/Findings.jsx";
import FindingPage from "./views/FindingPage.jsx";
import Module1Report from "./views/Module1Report.jsx";
import Module2Report from "./views/Module2Report.jsx";
import Module3Report from "./views/Module3Report.jsx";
import Calibration from "./views/Calibration.jsx";
import Operator from "./views/Operator.jsx";
import { api } from "./api/client.js";
import { connectAlerts } from "./api/socket.js";
import { matchRoute, useRoute } from "./lib/router.js";
import { OPEN_STATUSES } from "./lib/filters.js";
import { ANALYSTS } from "./lib/labels.js";
import { DEFAULT_USER } from "./config.js";
import { num } from "./lib/ui.js";

const MIN_RELOAD_MS = 10000; // zdarzenia z WebSocket przeladowuja dane najwyzej raz na 10 s

export default function App() {
  const route = useRoute();
  const view = matchRoute(route.path);
  const [reloadKey, setReloadKey] = useState(0);
  const [labels, setLabels] = useState([]);
  const [health, setHealth] = useState(null);
  const [openHigh, setOpenHigh] = useState(0);
  const [live, setLive] = useState(false);
  const [feed, setFeed] = useState([]);
  const [analyst, setAnalyst] = useState(DEFAULT_USER);
  const [toastState, setToastState] = useState(null);
  const toastTimer = useRef(null);
  const lastReload = useRef(0);
  const pendingReload = useRef(null);
  const wasLive = useRef(false);

  const reload = useCallback(() => {
    window.clearTimeout(pendingReload.current);
    pendingReload.current = null;
    lastReload.current = Date.now();
    setReloadKey((k) => k + 1);
  }, []);
  // Przeladowanie wywolane z zewnatrz (alert na zywo): nie czesciej niz MIN_RELOAD_MS.
  const reloadSoon = useCallback(() => {
    if (pendingReload.current) return;
    const wait = Math.max(0, MIN_RELOAD_MS - (Date.now() - lastReload.current));
    pendingReload.current = window.setTimeout(reload, wait);
  }, [reload]);

  const toast = useCallback((message, variant = "info", target = null) => {
    window.clearTimeout(toastTimer.current);
    setToastState({ message, variant, target });
    toastTimer.current = window.setTimeout(() => setToastState(null), variant === "success" ? 5600 : 4200);
  }, []);

  // "Odswiez dane": uzupelnij brakujace kadry filmow, potem przeladuj (blad kadrow nie blokuje odswiezenia).
  const refreshAll = useCallback(() => {
    api.backfillFrames()
      .then((r) => { if (r?.added) toast(`Uzupełniono kadry filmów: ${r.added}.`, "success"); })
      .catch(() => {})
      .finally(reload);
  }, [reload, toast]);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: "down" }));
    api.stats({ risk_level: "high", status: OPEN_STATUSES }).then((s) => setOpenHigh(s.total || 0)).catch(() => {});
  }, [reloadKey]);
  useEffect(() => { api.reviewLabels().then((r) => setLabels(r.items || [])).catch(() => setLabels([])); }, []);

  const dropped = useRef(false);
  const onLive = useCallback((on) => {
    setLive(on);
    if (!on && wasLive.current) {
      dropped.current = true;
      toast("Połączenie z alertami przerwane. Łączę ponownie…", "warning");
    }
    if (on && dropped.current) {
      dropped.current = false;
      toast("Połączono ponownie z alertami.", "success");
      reloadSoon(); // alerty z czasu przerwy: dociagnij dane
    }
    wasLive.current = on;
  }, [toast, reloadSoon]);

  useEffect(
    () =>
      connectAlerts({
        onState: onLive,
        onHigh: (raw) => {
          const a = { received_at: new Date().toISOString(), ...raw };
          setFeed((f) => [a, ...f.filter((x) => x.finding_id !== a.finding_id)].slice(0, 50));
          setOpenHigh((n) => n + 1);
          toast(`Wysokie ryzyko · ${num(a.risk_score)} · ${a.title || "nowy materiał"}`, "warning", a.finding_id);
          reloadSoon();
        },
        onNew: reloadSoon,
      }),
    [onLive, reloadSoon, toast],
  );

  const act = async (fn, okMessage) => {
    try {
      await fn();
      toast(okMessage, "success");
      reload();
    } catch (e) {
      toast(e.message || "Nie udało się zapisać zmiany.", "error");
      throw e;
    }
  };
  const onReview = (id, label, note) => act(() => api.review(id, label, note, analyst), "Decyzja zapisana w historii zmian.");
  const onAssign = (id, who) => act(() => api.assign(id, who, analyst), who ? `Przypisano: ${who}.` : "Zwolniono przypisanie.").catch(() => {});
  const onStatus = (id, status) => act(() => api.setStatus(id, status, analyst), "Status zmieniony.").catch(() => {});

  const common = { query: route.query, reloadKey, toast, analyst };
  const pages = {
    overview: () => <Overview onRefresh={refreshAll} onReview={onReview} {...common} />,
    alerts: () => <Alerts live={live} feed={feed} {...common} />,
    findings: () => <Findings {...common} />,
    finding: () => <FindingPage id={view.id} labels={labels} onReview={onReview} onAssign={onAssign} onStatus={onStatus} {...common} />,
    module1: () => <Module1Report {...common} />,
    module2: () => <Module2Report {...common} />,
    module3: () => <Module3Report {...common} />,
    calibration: () => <Calibration {...common} />,
    operator: () => <Operator {...common} />,
  };
  const page = pages[view.name]?.() || (
    <><PageHeader title="Nie znaleziono strony" lead={route.path} /><ErrorState message="Ten adres nie prowadzi do żadnej strony panelu." /></>
  );

  return (
    <>
      <Shell active={view.name === "finding" ? null : view.name} counts={{ alerts: openHigh }} health={health} live={live}
        analyst={analyst} analysts={[...new Set([...ANALYSTS, analyst])]} onAnalyst={setAnalyst}>
        <ErrorBoundary resetKey={route.path + reloadKey}>{page}</ErrorBoundary>
      </Shell>
      <div className={`toast ${toastState ? "visible" : ""} ${toastState && toastState.variant !== "info" ? toastState.variant : ""}`}
        role="status" aria-live="polite"
        onClick={() => { if (toastState?.target) window.location.hash = `#/findings/${encodeURIComponent(toastState.target)}`; }}
        style={toastState?.target ? { pointerEvents: "auto", cursor: "pointer" } : undefined}>
        {toastState?.message}
      </div>
    </>
  );
}
