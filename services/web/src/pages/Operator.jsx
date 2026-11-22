// Operator: kolejki analizy i limity skalowania (kontrakt B<->C, plan par. 6). Dane z /ops/scaling (proxy API).
import { useEffect, useState } from "react";
import { Alert, Badge, Button, Group, NumberInput, Paper, Stack, Table, Text, Title } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { getScaling, putScaling } from "../lib/api.js";
import { fmtShort } from "../lib/labels.js";

const STATE = { busy: "pracuje", idle: "czeka", starting: "uruchamia się", stopping: "zatrzymuje się" };

export default function Operator({ refreshKey }) {
  const [data, setData] = useState(null);
  const [draft, setDraft] = useState({});
  const [error, setError] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => getScaling()
    .then((d) => { setData(d); setError(null); })
    .catch((e) => setError(e.message));
  useEffect(() => {
    load();
    const t = window.setInterval(load, 5000); // stan autoskalera odswiezany co 5 s
    return () => window.clearInterval(t);
  }, [refreshKey]);

  const value = (q, k) => draft[q.name]?.[k] ?? q[k];
  const set = (q, k) => (v) => setDraft((d) => ({ ...d, [q.name]: { ...d[q.name], [k]: v } }));
  const dirty = Object.keys(draft).length > 0;

  const apply = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const queues = data.queues.filter((q) => draft[q.name]).map((q) => ({
        name: q.name, max: Number(value(q, "max")), cpus: Number(value(q, "cpus")), memory_mb: Number(value(q, "memory_mb")),
      }));
      const next = await putScaling({ queues });
      setData(next);
      setDraft({});
      notifications.show({ color: "green", message: "Limity skalowania zapisane.", autoClose: 4000 });
    } catch (e) {
      setSaveError(e.status === 422 ? e.message : `Nie zapisano: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Stack gap="sm">
      <Group justify="space-between" align="flex-end">
        <div>
          <Title order={1}>Operator</Title>
          <Text size="sm" c="dimmed">Kolejki analizy, kontenery analizatora i limity skalowania.</Text>
        </div>
        {data && (
          <Group gap="xs">
            {data.source === "atrapa" && <Badge color="orange" variant="light" title="AUTOSCALER_URL=atrapa: dane z kontraktu, nie z żywego autoskalera">atrapa kontraktu</Badge>}
            <Text size="sm">Wykonawca: <b>{data.executor}</b></Text>
            <Text size="sm">· równoległość Ollamy: <b>{data.ollama_parallel}</b></Text>
            <Text size="sm">· przepustowość: <b>{String(data.throughput_per_min).replace(".", ",")}</b>/min</Text>
          </Group>
        )}
      </Group>

      {error && <Alert color="gray" variant="light" title="Autoskaler niedostępny">{error}</Alert>}

      {data && (
        <>
          <Paper p="sm">
            <Title order={4} mb="xs">Kolejki</Title>
            <Table className="iw-table" verticalSpacing={6} highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Kolejka</Table.Th><Table.Th ta="right">Oczekuje</Table.Th><Table.Th ta="right">Działa</Table.Th>
                  <Table.Th ta="right">Min</Table.Th><Table.Th>Max kontenerów</Table.Th><Table.Th>CPU na kontener</Table.Th>
                  <Table.Th>RAM na kontener (MB)</Table.Th><Table.Th ta="right">Skaluj od kolejki</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {data.queues.map((q) => {
                  // Kolejki tylko do odczytu (q:ingest, q:render) maja cpus/memory_mb = null: bez edycji, "—".
                  const readOnly = q.cpus == null && q.memory_mb == null;
                  const dash = <Text size="sm" c="dimmed">—</Text>;
                  return (
                    <Table.Tr key={q.name}>
                      <Table.Td><code>{q.name}</code>{readOnly && <Text span size="xs" c="dimmed"> · tylko odczyt</Text>}</Table.Td>
                      <Table.Td ta="right">{q.backlog ?? "—"}</Table.Td>
                      <Table.Td ta="right">{q.running ?? "—"}</Table.Td>
                      <Table.Td ta="right">{q.min ?? "—"}</Table.Td>
                      <Table.Td>{readOnly ? (q.max ?? "—") : <NumberInput size="xs" w={90} min={q.min ?? 0} max={64} value={value(q, "max")} onChange={set(q, "max")} aria-label={`Maksimum kontenerów ${q.name}`} />}</Table.Td>
                      <Table.Td>{readOnly ? dash : <NumberInput size="xs" w={90} min={0.25} step={0.25} decimalScale={2} value={value(q, "cpus")} onChange={set(q, "cpus")} aria-label={`CPU ${q.name}`} />}</Table.Td>
                      <Table.Td>{readOnly ? dash : <NumberInput size="xs" w={110} min={256} step={256} value={value(q, "memory_mb")} onChange={set(q, "memory_mb")} aria-label={`RAM ${q.name}`} />}</Table.Td>
                      <Table.Td ta="right">{q.scale_up_backlog ?? "—"}</Table.Td>
                    </Table.Tr>
                  );
                })}
              </Table.Tbody>
            </Table>
            {saveError && <Text c="red" size="sm" mt="xs" role="alert">{saveError}</Text>}
            <Group justify="flex-end" mt="sm" gap="xs">
              {dirty && <Button variant="subtle" onClick={() => { setDraft({}); setSaveError(null); }}>Cofnij zmiany</Button>}
              <Button onClick={apply} disabled={!dirty} loading={saving}>Zastosuj</Button>
            </Group>
          </Paper>

          <Paper p="sm">
            <Title order={4} mb="xs">Kontenery analizatora ({data.workers.length})</Title>
            {data.workers.length ? (
              <Table className="iw-table" verticalSpacing={6}>
                <Table.Thead><Table.Tr><Table.Th>Kontener</Table.Th><Table.Th>Kolejka</Table.Th><Table.Th>Stan</Table.Th><Table.Th>Zadanie</Table.Th><Table.Th>Od</Table.Th></Table.Tr></Table.Thead>
                <Table.Tbody>
                  {data.workers.map((w) => (
                    <Table.Tr key={w.id}>
                      <Table.Td><code>{w.id}</code></Table.Td><Table.Td><code>{w.queue}</code></Table.Td>
                      <Table.Td>{STATE[w.state] || w.state}</Table.Td><Table.Td>{w.job || "—"}</Table.Td><Table.Td>{fmtShort(w.since)}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            ) : <Text size="sm" c="dimmed">Brak uruchomionych kontenerów analizatora.</Text>}
          </Paper>
        </>
      )}
    </Stack>
  );
}
