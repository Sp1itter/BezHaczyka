// Przeglad: liczniki z /stats, trend wykryc, podzial wg zrodla i poziomu ryzyka, najczesciej lamane reguly.
// Wszystko liczy serwer; panel pobiera tylko to, co pokazuje.
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import TrendChart from "../components/charts/TrendChart.jsx";
import Breakdown from "../components/charts/Breakdown.jsx";
import { EmptyState, PageHeader } from "../components/ui.jsx";
import RulesPanel from "../components/RulesPanel.jsx";
import { OPEN_STATUSES } from "../lib/filters.js";
import { RISK, RISK_COLOR, SOURCE } from "../lib/labels.js";
import { href } from "../lib/router.js";

const BUCKET = { "10min": "co 10 minut", hour: "na godzinę", day: "na dzień" };

function ChartPanel({ title, note, children, className = "" }) {
  return (
    <section className={`panel compact-panel ${className}`}>
      <div className="panel-head"><h2>{title}</h2>{note && <span className="quiet">{note}</span>}</div>
      <div className="chart-panel">{children}</div>
    </section>
  );
}

export default function Overview({ reloadKey }) {
  const all = useApi(() => api.stats(), [reloadKey]);
  const open = useApi(() => api.stats({ status: OPEN_STATUSES }), [reloadKey]);
  const trend = useApi(() => api.trend(), [reloadKey]);

  const s = all.data || {};
  const openHigh = open.data?.by_risk_level?.high || 0;
  const sources = Object.entries(s.by_source || {}).sort((a, b) => b[1] - a[1])
    .map(([k, v]) => ({ key: k, label: SOURCE[k] || k, value: v }));
  const risks = ["high", "medium", "low"].map((k) => ({ key: k, label: RISK[k], value: s.by_risk_level?.[k] || 0, color: RISK_COLOR[k] }));
  const kpis = [
    ["Przeanalizowane materiały", s.total ?? "—"],
    ["Wysokie ryzyko", s.by_risk_level?.high ?? 0, "kpi-high"],
    ["Czeka na decyzję", open.data?.total ?? "—"],
  ];

  return (
    <>
      <PageHeader title="Przegląd" lead="Bieżący stan analizy reklam inwestycyjnych." />

      <section className="kpi-bar kpi-3" aria-label="Najważniejsze liczby">
        {kpis.map(([label, value, cls]) => <div key={label} className={cls || ""}><span>{label}</span><strong>{value}</strong></div>)}
      </section>

      {openHigh > 0 && (
        <div className="notice warning">
          <div><strong>Materiały wysokiego ryzyka czekające na decyzję: {openHigh}</strong></div>
          <a href="#/alerts">Przejdź do alertów</a>
        </div>
      )}

      <div className="overview-grid">
        <ChartPanel className="span-12" title="Wykryte incydenty w czasie" note={`liczba wyników wg poziomu ryzyka, ${BUCKET[trend.data?.bucket] || "na dzień"}`}>
          {trend.data?.items?.length
            ? <TrendChart data={trend.data.items} variant="bar" height={220} />
            : <EmptyState size="compact">Wykres pojawi się po pierwszych analizach.</EmptyState>}
        </ChartPanel>

        <ChartPanel className="span-7" title="Źródła">
          {sources.length ? <Breakdown rows={sources} hrefFor={(k) => href("/findings", { source: k })} />
            : <EmptyState size="compact">Brak materiałów.</EmptyState>}
        </ChartPanel>
        <ChartPanel className="span-5" title="Poziom ryzyka">
          <Breakdown rows={risks} hrefFor={(k) => href("/findings", { risk: k })} />
        </ChartPanel>

        <div className="span-12 grid-cell"><RulesPanel allStats={all} /></div>
      </div>
    </>
  );
}
