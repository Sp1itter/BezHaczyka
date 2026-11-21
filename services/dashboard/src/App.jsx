import { useEffect, useMemo, useState } from "react";
import Sidebar from "./components/layout/Sidebar.jsx";
import TopBar, { RANGES } from "./components/layout/TopBar.jsx";
import FilterBar from "./components/layout/FilterBar.jsx";
import Flyout from "./components/common/Flyout.jsx";
import Toasts from "./components/common/Toasts.jsx";
import FindingDetail from "./components/findings/FindingDetail.jsx";
import Dashboard from "./views/Dashboard.jsx";
import Discover from "./views/Discover.jsx";
import Alerts from "./views/Alerts.jsx";
import Calibration from "./views/Calibration.jsx";
import { api } from "./api/client.js";
import { connectAlerts } from "./api/socket.js";
import { MODULE, RISK, SOURCE, STATUS } from "./lib/labels.js";
import { BRAND, NAV } from "./config.js";

const FILTER_GROUPS = [
  { key: "source", label: "Źródło", options: SOURCE },
  { key: "risk_level", label: "Ryzyko", options: RISK },
  { key: "module", label: "Moduł", options: MODULE },
  { key: "status", label: "Status", options: STATUS },
];

const VIEWS = { dashboard: Dashboard, discover: Discover, alerts: Alerts, calibration: Calibration };

// Zakres czasu -> from/to w ISO (format, ktory dostaje API).
function timeRange(range, custom) {
  if (range === "custom")
    return { from: custom.from ? `${custom.from}T00:00:00Z` : undefined, to: custom.to ? `${custom.to}T23:59:59Z` : undefined };
  const days = RANGES.find((r) => r.id === range)?.days || 30;
  return { from: new Date(Date.now() - days * 86400000).toISOString() };
}

export default function App() {
  const [view, setView] = useState("dashboard");
  const [q, setQ] = useState("");
  const [range, setRange] = useState("30d");
  const [custom, setCustom] = useState({ from: "", to: "" });
  const [filters, setFilters] = useState({});
  const [reloadKey, setReloadKey] = useState(0);
  const [threshold, setThreshold] = useState(65);
  const [selected, setSelected] = useState(null);
  const [live, setLive] = useState(false);
  const [feed, setFeed] = useState([]);
  const [toasts, setToasts] = useState([]);

  const query = useMemo(() => ({ ...timeRange(range, custom), q: q || undefined, ...filters }), [range, custom, q, filters, reloadKey]);
  const reload = () => setReloadKey((k) => k + 1);

  useEffect(
    () =>
      connectAlerts({
        onState: setLive,
        onHigh: (a) => {
          setFeed((f) => [a, ...f].slice(0, 50));
          setToasts((t) => [a, ...t].slice(0, 3));
          setTimeout(() => setToasts((t) => t.filter((x) => x.finding_id !== a.finding_id)), 10000);
          reload();
        },
        onNew: () => reload(),
      }),
    [],
  );

  const open = (id) => api.finding(id).then(setSelected);
  const update = async (id, patch) => {
    await api.updateFinding(id, patch);
    if (selected?.id === id) setSelected({ ...selected, ...patch });
    reload();
  };

  const nav = NAV.map((n) => (n.id === "alerts" ? { ...n, badge: feed.length || null } : n));
  const View = VIEWS[view];
  const title = NAV.find((n) => n.id === view)?.label;

  return (
    <div className="app">
      <Sidebar items={nav} active={view} onSelect={setView} brand={BRAND} />
      <main>
        <TopBar title={title} query={q} onQuery={setQ} range={range} onRange={setRange}
          custom={custom} onCustom={setCustom} onRefresh={reload} live={live} />
        {view !== "calibration" && (
          <FilterBar groups={FILTER_GROUPS} value={filters} onChange={setFilters} onClear={() => setFilters({})} />
        )}
        <div className="content">
          <View query={query} reloadKey={reloadKey} onOpen={open} onUpdate={update}
            live={live} feed={feed} threshold={threshold} onThreshold={setThreshold} />
        </div>
      </main>
      <Flyout open={!!selected} title="Szczegóły rekordu" onClose={() => setSelected(null)}>
        <FindingDetail finding={selected} onUpdate={update} />
      </Flyout>
      <Toasts items={toasts} onOpen={(id) => { open(id); setToasts((t) => t.filter((x) => x.finding_id !== id)); }}
        onDismiss={(id) => setToasts((t) => t.filter((x) => x.finding_id !== id))} />
    </div>
  );
}
