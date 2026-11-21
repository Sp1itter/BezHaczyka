import { useEffect, useState } from "react";
import { getHealth, subscribeAlerts } from "./lib/api.js";
import Findings from "./components/Findings.jsx";
import Overview from "./components/Overview.jsx";
import Calibration from "./components/Calibration.jsx";
import Alerts from "./components/Alerts.jsx";

const TABS = [
  ["findings", "Ustalenia"],
  ["overview", "Przegląd"],
  ["calibration", "Kalibracja"],
];

export default function App() {
  const [tab, setTab] = useState("findings");
  const [health, setHealth] = useState(null);
  const [live, setLive] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth({ status: "down" }));
  }, []);

  useEffect(
    () =>
      subscribeAlerts((msg) => {
        if (msg.type !== "finding.high") return;
        setAlerts((a) => [msg, ...a].slice(0, 5));
        setRefreshKey((k) => k + 1); // nowy alert => odswiez tabele
      }, setLive),
    [],
  );

  const openFinding = (id) => {
    setTab("findings");
    setSelected(id);
  };

  return (
    <div className="app">
      <header className="topbar">
        <h1>InvestWatch</h1>
        <span className="sub">Monitoring reklam inwestycyjnych</span>
        <span className="spacer" />
        <span className="pill" title="Stan API i bazy">
          <span className={`dot ${health?.status === "ok" ? "on" : health ? "off" : ""}`} />
          API {health ? (health.status === "ok" ? `ok (${health.dialect})` : "niedostępne") : "…"}
        </span>
        <span className="pill" title="Alerty WebSocket o wysokim ryzyku">
          <span className={`dot ${live ? "on" : "off"}`} />
          alerty {live ? "na żywo" : "rozłączone"}
        </span>
      </header>

      <nav className="tabs">
        {TABS.map(([id, label]) => (
          <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </nav>

      {tab === "findings" && (
        <Findings selected={selected} onSelect={setSelected} refreshKey={refreshKey} />
      )}
      {tab === "overview" && <Overview refreshKey={refreshKey} />}
      {tab === "calibration" && <Calibration />}

      <Alerts
        alerts={alerts}
        onOpen={(a) => {
          openFinding(a.finding_id);
          setAlerts((all) => all.filter((x) => x !== a));
        }}
      />
    </div>
  );
}
