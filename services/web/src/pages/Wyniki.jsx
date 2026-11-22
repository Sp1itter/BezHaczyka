// Wyniki: strona startowa (jury patrzy na nia najdluzej). Filtry w adresie, trend, gesta tabela
// ze stronicowaniem po stronie serwera, szuflada z naruszeniami po prawej.
import { useEffect, useMemo, useState } from "react";
import { Button, Grid, Group, Paper, Select, Stack, Text, TextInput, Title } from "@mantine/core";
import { DatePickerInput } from "@mantine/dates";
import { useDebouncedValue } from "@mantine/hooks";
import { MantineReactTable, useMantineReactTable } from "mantine-react-table";
import { MRT_Localization_PL } from "mantine-react-table/locales/pl/index.esm.mjs";
import dayjs from "dayjs";
import RiskBadge from "../components/RiskBadge.jsx";
import TrendStrip from "../components/TrendStrip.jsx";
import FindingDrawer from "../components/FindingDrawer.jsx";
import { getTrend, listFindings } from "../lib/api.js";
import { PAGE_SIZES, apiFilters, pageParams, toCsv } from "../lib/findings.js";
import { MODULE_SHORT, RISK, SOURCE, STATUS, fmtShort, publisherName, quiet, sourceLabel } from "../lib/labels.js";
import { navigate } from "../lib/router.js";

const opts = (obj) => Object.entries(obj).map(([value, label]) => ({ value, label }));
const SOURCES = opts({ facebook: SOURCE.facebook, instagram: SOURCE.instagram, youtube: SOURCE.youtube, www: SOURCE.www,
  tiktok: SOURCE.tiktok, tiktok_ads: SOURCE.tiktok_ads });
const RISKS = opts({ high: "Wysokie", medium: "Średnie", low: "Niskie" });
const MODULES = opts(MODULE_SHORT);
const STATUSES = opts(STATUS);

const failedNames = (f) => (f.rule_results || []).filter((r) => r.verdict === "fail")
  .sort((a, b) => (b.severity ?? 0) - (a.severity ?? 0)).map((r) => r.rule_name);

export default function Wyniki({ query, refreshKey, refresh, analyst }) {
  const [data, setData] = useState({ items: [], total: 0 });
  const [trend, setTrend] = useState([]);
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);
  const [search, setSearch] = useState(query.q || "");
  const [debounced] = useDebouncedValue(search, 300);
  const filters = apiFilters(query);
  const { pageIndex, pageSize, limit, offset } = pageParams(query);
  const key = JSON.stringify({ filters, limit, offset, refreshKey });

  const setQuery = (patch, resetPage = true) => {
    const next = { ...query, ...patch };
    if (resetPage) delete next.page;
    navigate("/wyniki", next, { replace: true });
  };

  useEffect(() => {
    if ((query.q || "") !== debounced) setQuery({ q: debounced });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced]);

  useEffect(() => {
    let alive = true;
    setState((s) => (s === "ok" ? "refreshing" : "loading"));
    Promise.all([listFindings({ ...filters, limit, offset }), getTrend(filters)])
      .then(([list, tr]) => { if (alive) { setData(list); setTrend(tr.items || []); setState("ok"); setError(null); } })
      .catch((e) => { if (alive) { setError(e.message); setState("error"); } });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const columns = useMemo(() => [
    { id: "date", header: "Data", size: 100, accessorFn: (f) => fmtShort(f.created_at) },
    { id: "risk", header: "Ryzyko", size: 120, Cell: ({ row }) => <RiskBadge level={row.original.risk_level} score={row.original.risk_score} /> },
    {
      id: "title", header: "Materiał", size: 320,
      Cell: ({ row }) => {
        const f = row.original;
        const title = quiet(f.document?.title) || quiet(f.document?.text_excerpt)?.slice(0, 90) || "Bez tytułu";
        return <Text size="sm" fw={500} lineClamp={1} title={title}>{title}</Text>;
      },
    },
    {
      id: "source", header: "Źródło", size: 200,
      accessorFn: (f) => `${sourceLabel(f.document?.source)} · ${publisherName(f.document) || "—"}`,
      Cell: ({ cell }) => <Text size="xs" c="dimmed" lineClamp={1} title={cell.getValue()}>{cell.getValue()}</Text>,
    },
    {
      id: "violations", header: "Naruszenia", size: 260,
      Cell: ({ row }) => {
        const names = failedNames(row.original);
        return names.length
          ? <Text size="xs" lineClamp={1} title={names.join(", ")}><b>{names.length}</b> · {names.slice(0, 2).join(", ")}{names.length > 2 ? "…" : ""}</Text>
          : <Text size="xs" c="dimmed">brak</Text>;
      },
    },
    { id: "module", header: "Moduł", size: 150, accessorFn: (f) => (f.modules || []).map((m) => MODULE_SHORT[m]).join(", ") || "—" },
    { id: "status", header: "Status", size: 110, accessorFn: (f) => STATUS[f.status] || f.status },
    { id: "assignee", header: "Przypisany", size: 110, accessorFn: (f) => f.assignee || "—" },
  ], []);

  const table = useMantineReactTable({
    columns,
    data: data.items,
    localization: MRT_Localization_PL,
    manualPagination: true,
    rowCount: data.total,
    state: {
      pagination: { pageIndex, pageSize }, isLoading: state === "loading", showProgressBars: state === "refreshing", density: "xs",
      // przy otwartej szufladzie zostaja kolumny potrzebne do wyboru wiersza
      columnVisibility: query.id ? { module: false, status: false, assignee: false, violations: false } : {},
    },
    onPaginationChange: (updater) => {
      const next = typeof updater === "function" ? updater({ pageIndex, pageSize }) : updater;
      setQuery({ page: next.pageIndex || undefined, size: next.pageSize }, false);
    },
    mantinePaginationProps: { rowsPerPageOptions: PAGE_SIZES.map(String), showRowsPerPage: true },
    enableSorting: false,
    enableColumnActions: false,
    enableColumnFilters: false,
    enableGlobalFilter: false,
    enableDensityToggle: false,
    enableFullScreenToggle: false,
    enableHiding: false,
    enableTopToolbar: false,
    mantineTableProps: { className: "iw-table", striped: false, highlightOnHover: true, withTableBorder: false },
    mantinePaperProps: { withBorder: true, shadow: "xs", radius: "xs" },
    mantineTableBodyRowProps: ({ row }) => ({
      onClick: () => setQuery({ id: row.original.id }, false),
      className: row.original.id === query.id ? "iw-row-selected" : undefined,
      style: { cursor: "pointer", height: 32 },
      tabIndex: 0,
      onKeyDown: (e) => { if (e.key === "Enter") setQuery({ id: row.original.id }, false); },
    }),
    renderEmptyRowsFallback: () => (
      <Text size="sm" c="dimmed" p="lg">{state === "error" ? `Nie udało się pobrać wyników: ${error}` : "Brak wyników dla wybranych filtrów."}</Text>
    ),
  });

  const exportCsv = async () => {
    const all = await listFindings({ ...filters, limit: 500, offset: 0 });
    const csv = toCsv(all.items, [
      { label: "Data", value: (f) => f.created_at },
      { label: "Ryzyko", value: (f) => RISK[f.risk_level] },
      { label: "Wynik", value: (f) => f.risk_score },
      { label: "Tytuł", value: (f) => quiet(f.document?.title) },
      { label: "Źródło", value: (f) => sourceLabel(f.document?.source) },
      { label: "Publikujący", value: (f) => publisherName(f.document) },
      { label: "URL", value: (f) => f.document?.url },
      { label: "Naruszenia", value: (f) => failedNames(f).join(" | ") },
      { label: "Status", value: (f) => STATUS[f.status] },
    ]);
    const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: `wyniki-${dayjs().format("YYYY-MM-DD")}.csv` });
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const range = [query.from ? dayjs(query.from).toDate() : null, query.to ? dayjs(query.to).toDate() : null];
  const active = ["from", "to", "source", "risk", "module", "status", "q"].some((k) => query[k]);

  return (
    <Stack gap="sm">
      <Group justify="space-between" align="flex-end">
        <div>
          <Title order={1}>Wyniki</Title>
          <Text size="sm" c="dimmed">{state === "loading" ? "Wczytywanie…" : `${data.total} wyników dla wybranych filtrów`}</Text>
        </div>
        <Group gap="xs">
          {active && <Button variant="subtle" onClick={() => { setSearch(""); navigate("/wyniki", {}, { replace: true }); }}>Wyczyść filtry</Button>}
          <Button variant="default" onClick={exportCsv} disabled={!data.total}>Pobierz CSV</Button>
        </Group>
      </Group>

      <Paper p="sm">
        <Group gap="sm" align="flex-end" wrap="wrap">
          <DatePickerInput type="range" label="Zakres dat" placeholder="dowolny" clearable valueFormat="DD.MM.YYYY" w={230}
            value={range} onChange={([a, b]) => setQuery({ from: a ? dayjs(a).format("YYYY-MM-DD") : undefined, to: b ? dayjs(b).format("YYYY-MM-DD") : undefined })} />
          <Select label="Źródło" placeholder="wszystkie" data={SOURCES} clearable w={150} value={query.source || null} onChange={(v) => setQuery({ source: v || undefined })} />
          <Select label="Ryzyko" placeholder="wszystkie" data={RISKS} clearable w={130} value={query.risk || null} onChange={(v) => setQuery({ risk: v || undefined })} />
          <Select label="Moduł" placeholder="wszystkie" data={MODULES} clearable w={200} value={query.module || null} onChange={(v) => setQuery({ module: v || undefined })} />
          <Select label="Status" placeholder="wszystkie" data={STATUSES} clearable w={140} value={query.status || null} onChange={(v) => setQuery({ status: v || undefined })} />
          <TextInput label="Szukaj" placeholder="tytuł, treść, adres" w={220} value={search} onChange={(e) => setSearch(e.currentTarget.value)} />
        </Group>
      </Paper>

      <Paper p="sm">
        <Group justify="space-between" mb={2}>
          <Text size="sm" fw={600}>Wyniki na dzień</Text>
          <Text size="xs" c="dimmed">wysokie · średnie · niskie · doba wg UTC</Text>
        </Group>
        <TrendStrip items={trend} />
      </Paper>

      <Grid gutter="sm" align="flex-start">
        <Grid.Col span={query.id ? { base: 12, lg: "auto" } : 12} style={{ minWidth: 0 }}>
          <MantineReactTable table={table} />
        </Grid.Col>
        {query.id && (
          <Grid.Col span={{ base: 12, lg: "content" }} style={{ width: 480, maxWidth: "100%" }}>
            <FindingDrawer id={query.id} analyst={analyst} onClose={() => setQuery({ id: undefined }, false)} onChanged={refresh} />
          </Grid.Col>
        )}
      </Grid>
    </Stack>
  );
}
