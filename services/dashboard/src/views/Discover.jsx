import Panel from "../components/common/Panel.jsx";
import TrendChart from "../components/charts/TrendChart.jsx";
import FindingsTable from "../components/findings/FindingsTable.jsx";
import { api } from "../api/client.js";
import { useApi } from "../hooks/useApi.js";

// Widok "Wyniki" (Discover): histogram w czasie + tabela rekordow.
export default function Discover({ query, reloadKey, onOpen, onUpdate }) {
  const key = JSON.stringify(query) + reloadKey;
  const list = useApi(() => api.findings(query), [key]);
  const trend = useApi(() => api.trend(query), [key]);
  return (
    <>
      <Panel title={`Wyniki: ${list.data?.total ?? "…"}`}>
        <TrendChart data={trend.data?.items || []} variant="bar" height={160} />
      </Panel>
      <Panel>
        {list.error ? <div className="empty">Błąd API: {list.error.message}</div> :
          <FindingsTable items={list.data?.items} onOpen={onOpen} onStatusChange={onUpdate} />}
      </Panel>
    </>
  );
}
