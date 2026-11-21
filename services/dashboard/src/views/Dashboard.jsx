import Panel from "../components/common/Panel.jsx";
import StatTile from "../components/common/StatTile.jsx";
import TrendChart from "../components/charts/TrendChart.jsx";
import Breakdown from "../components/charts/Breakdown.jsx";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";
import { MODULE, RISK, RISK_COLOR, SOURCE, STATUS } from "../lib/labels.js";

export default function Dashboard({ query, reloadKey }) {
  const key = JSON.stringify(query) + reloadKey;
  const stats = useApi(() => api.stats(query), [key]);
  const trend = useApi(() => api.trend(query), [key]);
  const s = stats.data || {};
  const rules = Object.fromEntries((s.failed_rules || []).slice(0, 6).map((r) => [`${r.rule_id}. ${r.rule_name}`, r.count]));
  const open = (s.by_status?.new || 0) + (s.by_status?.triage || 0) + (s.by_status?.in_review || 0);
  return (
    <div className="grid">
      <div className="tiles span-12">
        <StatTile label="Wszystkie wyniki" value={s.total ?? "…"} />
        <StatTile label="Wysokie ryzyko" value={s.by_risk_level?.high ?? 0} color={RISK_COLOR.high} />
        <StatTile label="Otwarte sprawy" value={open} hint="nowe + triage + w analizie" />
        <StatTile label="Potwierdzone" value={s.by_status?.confirmed ?? 0} />
      </div>
      <Panel title="Wykryte incydenty w czasie" className="span-12">
        <TrendChart data={trend.data?.items || []} height={260} />
      </Panel>
      <Panel title="Poziom ryzyka" className="span-4"><Breakdown data={s.by_risk_level} labels={RISK} colors={RISK_COLOR} /></Panel>
      <Panel title="Źródło" className="span-4"><Breakdown data={s.by_source} labels={SOURCE} /></Panel>
      <Panel title="Moduł analityczny" className="span-4"><Breakdown data={s.by_module} labels={MODULE} /></Panel>
      <Panel title="Status spraw" className="span-6"><Breakdown data={s.by_status} labels={STATUS} /></Panel>
      <Panel title="Najczęściej naruszane reguły" className="span-6"><Breakdown data={rules} height={220} /></Panel>
    </div>
  );
}
