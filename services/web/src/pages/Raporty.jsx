// Raporty: zakladki Modul 1 (podmioty trzecie, /reports/module1) i Modul 3 (/reports/module3). Eksport CSV.
import { useEffect, useMemo, useState } from "react";
import { Alert, Anchor, Badge, Button, Group, Paper, Select, Stack, Tabs, Text, Title } from "@mantine/core";
import { MantineReactTable, useMantineReactTable } from "mantine-react-table";
import { MRT_Localization_PL } from "mantine-react-table/locales/pl/index.esm.mjs";
import { getModule1Report, getModule3Report, module3CsvUrl } from "../lib/api.js";
import { FLAGS, clip, csvUrl, flagLabel, safeHref, summarize } from "../lib/module1.js";
import { RELATION, SOURCE, fmtShort, quiet, sourceLabel } from "../lib/labels.js";
import { navigate } from "../lib/router.js";

const opts = (obj) => Object.entries(obj).map(([value, label]) => ({ value, label }));

function ReportTable({ columns, rows, loading, empty }) {
  const table = useMantineReactTable({
    columns, data: rows, localization: MRT_Localization_PL,
    enableColumnActions: false, enableColumnFilters: false, enableDensityToggle: false, enableFullScreenToggle: false,
    enableHiding: false, enableTopToolbar: false, enableGlobalFilter: false,
    initialState: { density: "xs", pagination: { pageIndex: 0, pageSize: 50 } },
    state: { isLoading: loading },
    mantineTableProps: { className: "iw-table", highlightOnHover: true, withTableBorder: false },
    mantinePaperProps: { withBorder: true, shadow: "xs", radius: "xs" },
    renderEmptyRowsFallback: () => <Text size="sm" c="dimmed" p="lg">{empty}</Text>,
  });
  return <MantineReactTable table={table} />;
}

const link = (href, text) => (safeHref(href) ? <Anchor size="sm" href={safeHref(href)} target="_blank" rel="noreferrer noopener">{text}</Anchor> : text);

function Module1({ query }) {
  const filters = { source: query.source || "", relation: query.relation || "", flag: query.flag || "" };
  const [data, setData] = useState({ items: [], total: 0 });
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  const key = JSON.stringify(filters);
  useEffect(() => {
    let ignore = false;
    setState("loading");
    getModule1Report(filters)
      .then((d) => { if (!ignore) { setData(d); setState("ok"); setError(null); } })
      .catch((e) => { if (!ignore) { setData({ items: [], total: 0 }); setState("error"); setError(e.message); } });
    return () => { ignore = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  const set = (k) => (v) => navigate("/raporty", { ...query, tab: "m1", [k]: v || undefined }, { replace: true });
  const s = summarize(data.items, data.total);
  const columns = useMemo(() => [
    { id: "firm", header: "Firma", size: 200, accessorFn: (r) => `${r.firm_official_name || r.firm_name_in_ad || "—"}${r.firm_country ? ` (${r.firm_country})` : ""}` },
    { id: "adv", header: "Reklamujący", size: 180, accessorFn: (r) => r.advertiser_name || r.advertiser_handle || r.advertiser_url || "—",
      Cell: ({ row, cell }) => link(row.original.advertiser_url, cell.getValue()) },
    { id: "rel", header: "Relacja", size: 120, accessorFn: (r) => RELATION[r.relation] || r.relation || "—" },
    { id: "flags", header: "Flagi", size: 200, accessorFn: (r) => (r.m1_flags || []).map(flagLabel).join(", "),
      Cell: ({ row }) => ((row.original.m1_flags || []).length
        ? <Group gap={4}>{row.original.m1_flags.map((f) => <Badge key={f} color="gray" size="xs">{flagLabel(f)}</Badge>)}</Group>
        : <Text size="xs" c="dimmed">—</Text>) },
    { id: "text", header: "Treść", size: 280, accessorFn: (r) => quiet(clip(r.tresc)) },
    { id: "url", header: "URL", size: 80, enableSorting: false, accessorFn: (r) => r.url, Cell: ({ row }) => link(row.original.url, "otwórz") },
    { id: "platforms", header: "Źródło", size: 100, accessorFn: (r) => sourceLabel(r.source) },
    { id: "last", header: "Ostatnio widziane", size: 130, accessorFn: (r) => r.last_seen_at || "", Cell: ({ row }) => fmtShort(row.original.last_seen_at) },
  ], []);
  return (
    <Stack gap="sm">
      <Paper p="sm">
        <Group gap="sm" align="flex-end" justify="space-between">
          <Group gap="sm" align="flex-end">
            <Select label="Źródło" placeholder="wszystkie" data={opts(SOURCE)} clearable w={160} value={query.source || null} onChange={set("source")} />
            <Select label="Relacja" placeholder="wszystkie" data={opts(RELATION)} clearable w={180} value={query.relation || null} onChange={set("relation")} />
            <Select label="Flaga" placeholder="wszystkie" data={opts(FLAGS)} clearable w={220} value={query.flag || null} onChange={set("flag")} />
          </Group>
          <Button component="a" variant="default" href={csvUrl(filters)} download>Pobierz CSV</Button>
        </Group>
      </Paper>
      {state === "ok" && <Text size="sm" c="dimmed">{s.total} pozycji · na stronie: {s.thirdParty} podmiotów trzecich, {s.noDisclosure} bez ujawnienia współpracy, {s.foreign} firm zagranicznych</Text>}
      {state === "error" && <Alert color="gray" variant="light">{error}</Alert>}
      <ReportTable columns={columns} rows={data.items} loading={state === "loading"} empty="Brak pozycji dla wybranych filtrów." />
    </Stack>
  );
}

function Module3() {
  const [data, setData] = useState({ items: [], total: 0 });
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  useEffect(() => {
    getModule3Report().then((d) => { setData(d); setState("ok"); }).catch((e) => { setState("error"); setError(e.message); });
  }, []);
  const columns = useMemo(() => [
    { id: "who", header: "Podmiot", size: 200, accessorFn: (r) => r.entity || r.publisher || "—" },
    { id: "offer", header: "Treść oferty", size: 360, accessorFn: (r) => quiet(clip(r.offer_text || r.text)) },
    { id: "url", header: "URL", size: 80, enableSorting: false, accessorFn: (r) => r.url, Cell: ({ row }) => link(row.original.url, "otwórz") },
    { id: "knf", header: "Rejestr KNF", size: 180, accessorFn: (r) => r.registry_status || "—" },
    { id: "date", header: "Wykryto", size: 130, accessorFn: (r) => r.created_at || "", Cell: ({ row }) => fmtShort(row.original.created_at) },
  ], []);
  return (
    <Stack gap="sm">
      <Group justify="space-between">
        <Text size="sm" c="dimmed">Materiały, w których analizator stwierdził doradztwo inwestycyjne bez zezwolenia KNF.</Text>
        <Button component="a" variant="default" href={module3CsvUrl()} download disabled={state !== "ok" || !data.total}>Pobierz CSV</Button>
      </Group>
      {state === "error" && <Alert color="gray" variant="light">{error}</Alert>}
      <ReportTable columns={columns} rows={data.items} loading={state === "loading"} empty="Brak pozycji Modułu 3." />
    </Stack>
  );
}

export default function Raporty({ query }) {
  const tab = query.tab === "m3" ? "m3" : "m1";
  return (
    <Stack gap="sm">
      <Title order={1}>Raporty</Title>
      <Tabs value={tab} onChange={(v) => navigate("/raporty", { tab: v }, { replace: true })} keepMounted={false}>
        <Tabs.List>
          <Tabs.Tab value="m1">Moduł 1 · podmioty trzecie</Tabs.Tab>
          <Tabs.Tab value="m3">Moduł 3 · doradztwo bez zezwolenia</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="m1" pt="sm"><Module1 query={query} /></Tabs.Panel>
        <Tabs.Panel value="m3" pt="sm"><Module3 /></Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
