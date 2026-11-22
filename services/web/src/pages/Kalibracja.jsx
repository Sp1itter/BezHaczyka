// Kalibracja: prog flagowania na zbiorze zlotym (GET /calibration), metryki liczone w przegladarce (metrics.js),
// zapis progu alertow po stronie serwera (PUT /settings/threshold).
import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Grid, Group, Paper, Slider, Stack, Table, Text, Title } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getCalibration, getThreshold, putThreshold } from "../lib/api.js";
import { bestF1, confusion, scores, sweep } from "../lib/metrics.js";
import { TOKENS } from "../theme.js";

const f2 = (v) => (v == null ? "—" : v.toFixed(2).replace(".", ","));
const SMALL_SAMPLE = 30;

function Metric({ label, value, hint }) {
  return (
    <div>
      <Text size="xs" c="dimmed">{label}</Text>
      <Text fw={600} size="xl">{value}</Text>
      {hint && <Text size="xs" c="dimmed">{hint}</Text>}
    </div>
  );
}

export default function Kalibracja() {
  const [gold, setGold] = useState(null);
  const [error, setError] = useState(null);
  const [threshold, setThresholdState] = useState(null);
  const [saved, setSaved] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getCalibration().then(setGold).catch((e) => setError(e.message));
    getThreshold().then((t) => setSaved(t.value)).catch(() => setSaved(null));
  }, []);

  const items = useMemo(() => gold?.items || [], [gold]);
  const rows = useMemo(() => sweep(items, 1), [items]);
  const best = useMemo(() => bestF1(rows), [rows]);
  useEffect(() => {
    if (threshold == null && best) setThresholdState(best.threshold); // domyslnie najlepsze F1
  }, [best, threshold]);

  if (error) return <Alert color="gray" title="Brak zbioru złotego">{error}</Alert>;
  if (!gold) return <Text c="dimmed">Wczytywanie zbioru złotego…</Text>;
  const t = threshold ?? 50;
  const m = confusion(items, t);
  const s = scores(m);
  const scored = items.filter((i) => typeof i.score === "number");

  const save = async () => {
    setSaving(true);
    try {
      const r = await putThreshold(t);
      setSaved(r.value);
      notifications.show({ color: "green", message: `Próg alertów ustawiony na ${r.value}.`, autoClose: 4000 });
    } catch (e) {
      notifications.show({ color: "red", title: "Nie zapisano progu", message: e.message, autoClose: 8000 });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Stack gap="sm">
      <Group justify="space-between" align="flex-end">
        <div>
          <Title order={1}>Kalibracja</Title>
          <Text size="sm" c="dimmed">Zbiór złoty: {items.length} materiałów z oceną człowieka, {scored.length} z wynikiem analizatora.</Text>
        </div>
        <Group gap="xs">
          <Text size="sm" c="dimmed">Obecny próg alertów: <b>{saved ?? "—"}</b></Text>
          <Button onClick={save} loading={saving} disabled={saved === t}>Zapisz {t} jako próg alertów</Button>
        </Group>
      </Group>

      {items.length < SMALL_SAMPLE && (
        <Alert color="orange" variant="light" p="xs">
          Mała próba ({items.length} pozycji): jedna etykieta zmienia F1 o kilka dziesiątych. Wyniki traktuj orientacyjnie.
        </Alert>
      )}

      <Paper p="md">
        <Group justify="space-between" mb="xs">
          <Text fw={600}>Flaguj materiał, gdy wynik ryzyka ≥ {t}</Text>
          {best && <Button size="xs" variant="subtle" onClick={() => setThresholdState(best.threshold)}>Najlepsze F1: próg {best.threshold} (F1 {f2(best.f1)})</Button>}
        </Group>
        <Slider min={0} max={100} step={1} value={t} onChange={setThresholdState} label={(v) => `próg ${v}`}
          marks={[{ value: 0, label: "0" }, { value: 50, label: "50" }, { value: 100, label: "100" }]} mb="lg" />
        <Group gap={48} mt="md">
          <Metric label="Precyzja" value={f2(s.precision)} hint="ile oflagowanych to naruszenia" />
          <Metric label="Pełność" value={f2(s.recall)} hint="ile naruszeń oflagowano" />
          <Metric label="F1" value={f2(s.f1)} />
          <Metric label="Oflagowane" value={`${m.tp + m.fp} z ${scored.length}`} />
        </Group>
      </Paper>

      <Grid gutter="sm">
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper p="md" h="100%">
            <Title order={4} mb="xs">Macierz pomyłek</Title>
            <Table withColumnBorders withTableBorder className="iw-table">
              <Table.Thead><Table.Tr><Table.Th /><Table.Th>naruszenie</Table.Th><Table.Th>bez naruszenia</Table.Th></Table.Tr></Table.Thead>
              <Table.Tbody>
                <Table.Tr><Table.Th>oflagowane</Table.Th><Table.Td><b>{m.tp}</b> trafienia</Table.Td><Table.Td><b>{m.fp}</b> fałszywe alarmy</Table.Td></Table.Tr>
                <Table.Tr><Table.Th>pominięte</Table.Th><Table.Td><b>{m.fn}</b> przeoczenia</Table.Td><Table.Td><b>{m.tn}</b> poprawnie</Table.Td></Table.Tr>
              </Table.Tbody>
            </Table>
          </Paper>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Paper p="md">
            <Title order={4} mb="xs">Fałszywe alarmy i przeoczenia w funkcji progu</Title>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={rows} margin={{ top: 6, right: 12, left: -20, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke={TOKENS.border} />
                <XAxis dataKey="threshold" type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: TOKENS.muted }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: TOKENS.muted }} />
                <Tooltip labelFormatter={(v) => `próg ${v}`} contentStyle={{ fontSize: 12, borderRadius: 4 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine x={t} stroke={TOKENS.accent} strokeDasharray="4 3" />
                <Line dataKey="fp" name="fałszywe alarmy (FP)" stroke={TOKENS.risk.medium} dot={false} isAnimationActive={false} type="stepAfter" />
                <Line dataKey="fn" name="przeoczenia (FN)" stroke={TOKENS.risk.high} dot={false} isAnimationActive={false} type="stepAfter" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid.Col>
      </Grid>

      <Paper p="md">
        <Title order={4} mb="xs">Zbiór złoty przy progu {t}</Title>
        <Table className="iw-table" verticalSpacing={6} highlightOnHover>
          <Table.Thead><Table.Tr><Table.Th>ID</Table.Th><Table.Th ta="right">Wynik</Table.Th><Table.Th>Ocena człowieka</Table.Th><Table.Th>System</Table.Th><Table.Th>Uzasadnienie oceny</Table.Th></Table.Tr></Table.Thead>
          <Table.Tbody>
            {[...items].sort((a, b) => (b.score ?? -1) - (a.score ?? -1)).map((it) => {
              const has = typeof it.score === "number";
              const flagged = has && it.score >= t;
              const ok = has && flagged === Boolean(it.is_violation);
              return (
                <Table.Tr key={it.id}>
                  <Table.Td><Text size="xs" ff="monospace">{it.id}</Text></Table.Td>
                  <Table.Td ta="right">{has ? it.score.toFixed(1).replace(".", ",") : "—"}</Table.Td>
                  <Table.Td>{it.is_violation ? "naruszenie" : "bez naruszenia"}</Table.Td>
                  <Table.Td><Text size="sm" c={!has ? "dimmed" : ok ? undefined : "red"}>{!has ? "brak wyniku" : flagged ? "oflagowane" : "pominięte"}{has && !ok ? " (błąd)" : ""}</Text></Table.Td>
                  <Table.Td><Text size="xs" lineClamp={2} title={it.note || ""}>{it.note}</Text></Table.Td>
                </Table.Tr>
              );
            })}
          </Table.Tbody>
        </Table>
      </Paper>
    </Stack>
  );
}
