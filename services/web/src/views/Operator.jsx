// Operator: kolejki, limity kontenerow analizy i workery z GET /ops/scaling (proxy API do autoskalera).
// Edytowalna jest tylko kolejka analizy (q:gpu); kolejki tylko do odczytu maja cpus/memory_mb = null.
import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { EmptyState, PageHeader } from "../components/ui.jsx";
import { fmtDate } from "../lib/labels.js";
import { num } from "../lib/ui.js";

const REFRESH_MS = 10000; // nie czesciej niz co 10 s
const STATE = { busy: "pracuje", idle: "czeka", starting: "uruchamia się", stopping: "zatrzymuje się" };
const QUEUE = { "q:gpu": "analiza (model)", "q:ingest": "wyszukiwanie materiałów", "q:render": "pobieranie i zrzuty" };
const readOnly = (q) => q.cpus == null && q.memory_mb == null;

export default function Operator({ toast }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [draft, setDraft] = useState({});
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () => api.scaling()
      .then((d) => { if (alive) { setData(d); setError(null); } })
      .catch((e) => { if (alive) setError(e.message); });
    load();
    const t = window.setInterval(load, REFRESH_MS);
    return () => { alive = false; window.clearInterval(t); };
  }, []);

  const value = (q, k) => draft[q.name]?.[k] ?? q[k] ?? "";
  const set = (q, k) => (e) => setDraft((d) => ({ ...d, [q.name]: { ...d[q.name], [k]: e.target.value } }));
  const dirty = Object.keys(draft).length > 0;

  const apply = async () => {
    setSaving(true);
    setSaveError("");
    try {
      const queues = data.queues.filter((q) => draft[q.name] && !readOnly(q)).map((q) => ({
        name: q.name, max: Number(value(q, "max")), cpus: Number(value(q, "cpus")), memory_mb: Number(value(q, "memory_mb")),
      }));
      setData(await api.saveScaling({ queues }));
      setDraft({});
      toast("Limity zapisane.", "success");
    } catch (e) {
      setSaveError(e.status === 422 ? `Nieprawidłowe wartości: ${e.message}` : `Nie zapisano: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <PageHeader title="Operator" lead="Kolejki pracy, limity kontenerów analizy i stan workerów. Odświeżane co 10 s." />
      {error && <EmptyState title="Autoskaler niedostępny">{error}</EmptyState>}
      {data && (
        <>
          <section className="kpi-bar" aria-label="Stan analizy">
            {data.throughput_per_min != null && <div><span>Przepustowość</span><strong>{num(data.throughput_per_min)} / min</strong></div>}
            {data.ollama_parallel != null && <div><span>Równoległe zapytania do modelu</span><strong>{data.ollama_parallel}</strong></div>}
            <div><span>Workery</span><strong>{data.workers.length}</strong></div>
          </section>
          {data.source === "atrapa" && <div className="notice"><div><strong>Dane przykładowe z kontraktu</strong> — autoskaler nie jest podłączony.</div></div>}

          <section className="panel table-panel">
            <div className="panel-head"><h2>Kolejki</h2></div>
            <div className="table-wrap">
              <table className="ops-table">
                <thead><tr><th>Kolejka</th><th className="num">Oczekuje</th><th className="num">Działa</th><th>Max kontenerów</th><th>CPU na kontener</th><th>RAM na kontener (MB)</th></tr></thead>
                <tbody>
                  {data.queues.map((q) => (
                    <tr key={q.name}>
                      <td><strong>{QUEUE[q.name] || q.name}</strong><span className="table-meta">{q.name}{readOnly(q) ? " · tylko odczyt" : ""}</span></td>
                      <td className="num">{q.backlog ?? "—"}</td>
                      <td className="num">{q.running ?? "—"}</td>
                      <td>{readOnly(q) ? (q.max ?? "—")
                        : <input type="number" min={q.min ?? 0} max="64" value={value(q, "max")} onChange={set(q, "max")} aria-label={`Maksimum kontenerów ${q.name}`} />}</td>
                      <td>{readOnly(q) ? "—"
                        : <input type="number" min="0.25" step="0.25" value={value(q, "cpus")} onChange={set(q, "cpus")} aria-label={`CPU ${q.name}`} />}</td>
                      <td>{readOnly(q) ? "—"
                        : <input type="number" min="256" step="256" value={value(q, "memory_mb")} onChange={set(q, "memory_mb")} aria-label={`RAM ${q.name}`} />}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {saveError && <p className="form-error" role="alert">{saveError}</p>}
            <div className="form-actions">
              {dirty && <button type="button" className="button ghost" onClick={() => { setDraft({}); setSaveError(""); }}>Cofnij zmiany</button>}
              <button type="button" className="button primary" disabled={!dirty || saving} onClick={apply}>Zastosuj</button>
            </div>
          </section>

          <section className="panel table-panel top-gap">
            <div className="panel-head"><h2>Workery (wszystkie kolejki): {data.workers.length}</h2></div>
            {data.workers.length ? (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Kontener</th><th>Kolejka</th><th>Stan</th><th>Zadanie</th><th>Od</th></tr></thead>
                  <tbody>
                    {data.workers.map((w) => (
                      <tr key={w.id}>
                        <td><code>{w.id}</code></td><td>{QUEUE[w.queue] || w.queue}</td>
                        <td>{STATE[w.state] || w.state}</td><td>{w.job || "—"}</td><td className="nowrap">{w.since ? fmtDate(w.since) : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState size="compact">Brak uruchomionych workerów.</EmptyState>}
          </section>
        </>
      )}
    </>
  );
}
