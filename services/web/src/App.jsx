import { useCallback, useEffect, useState } from "react";
import { AppShell, Badge, Group, Image, NativeSelect, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { getHealth, subscribeAlerts } from "./lib/api.js";
import { pageOf, useRoute } from "./lib/router.js";
import { quiet } from "./lib/labels.js";
import Wyniki from "./pages/Wyniki.jsx";
import Alerty from "./pages/Alerty.jsx";
import Kalibracja from "./pages/Kalibracja.jsx";
import Raporty from "./pages/Raporty.jsx";
import Operator from "./pages/Operator.jsx";

const NAV = [
  ["wyniki", "Wyniki"],
  ["alerty", "Alerty"],
  ["kalibracja", "Kalibracja"],
  ["raporty", "Raporty"],
  ["operator", "Operator"],
];
// Analityk do czasu logowania: decyzje zapisuja sie na to konto (PATCH actor).
const ANALYSTS = ["analityk.a", "analityk.b", "analityk.c"];

function storedAnalyst() {
  try {
    return window.localStorage.getItem("iw-analyst") || ANALYSTS[0];
  } catch {
    return ANALYSTS[0];
  }
}

export default function App() {
  const route = useRoute();
  const page = pageOf(route.path);
  const [health, setHealth] = useState(null);
  const [live, setLive] = useState(false);
  const [feed, setFeed] = useState([]);
  const [unread, setUnread] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [analyst, setAnalystState] = useState(storedAnalyst);

  const setAnalyst = (a) => {
    setAnalystState(a);
    try {
      window.localStorage.setItem("iw-analyst", a);
    } catch {
      /* brak localStorage: wybor tylko w tej karcie */
    }
  };
  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth({ status: "down" }));
  }, [refreshKey]);

  useEffect(
    () =>
      subscribeAlerts((msg) => {
        if (msg.type !== "finding.high") return;
        const a = { received_at: new Date().toISOString(), ...msg };
        setFeed((f) => [a, ...f.filter((x) => x.finding_id !== a.finding_id)].slice(0, 200));
        setUnread((n) => n + 1);
        notifications.show({
          color: "red",
          title: `Wysokie ryzyko · ${Number(a.risk_score ?? 0).toFixed(1).replace(".", ",")}`,
          message: quiet(a.title) || a.document_id,
          autoClose: 8000,
          style: { cursor: "pointer" },
          onClick: () => { window.location.hash = `#/wyniki?id=${encodeURIComponent(a.finding_id)}`; },
        });
        refresh();
      }, setLive),
    [refresh],
  );

  useEffect(() => {
    if (page === "alerty") setUnread(0);
  }, [page]);

  const props = { query: route.query, refreshKey, refresh, analyst };
  return (
    <AppShell header={{ height: 52 }} padding="md">
      <AppShell.Header style={{ borderBottom: "1px solid var(--iw-border)" }}>
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group gap={28} wrap="nowrap">
            <a href="#/wyniki" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none", color: "inherit" }}>
              <Image src="brand/bezhaczyka-ikona.png" alt="" w={26} h={26} radius={6} />
              <div style={{ lineHeight: 1.1 }}>
                <Text fw={600} size="md">BezHaczyka</Text>
                <Text c="dimmed" size="xs">InvestWatch · UKNF</Text>
              </div>
            </a>
            <nav aria-label="Strony panelu" style={{ display: "flex" }}>
              {NAV.map(([id, label]) => (
                <a key={id} href={`#/${id}`} className="iw-nav-link" aria-current={page === id ? "page" : undefined}>
                  {label}
                  {id === "alerty" && unread > 0 && <Badge size="xs" color="red" variant="filled">{unread}</Badge>}
                </a>
              ))}
            </nav>
          </Group>
          <Group gap="md" wrap="nowrap">
            <NativeSelect size="xs" aria-label="Zalogowany analityk" data={ANALYSTS} value={analyst}
              onChange={(e) => setAnalyst(e.currentTarget.value)} />
            <Group gap={6} wrap="nowrap" title={health?.status === "ok" ? `API: ${health.dialect}` : "API niedostępne"}>
              <span className="iw-live-dot" data-on={String(live)} />
              <Text size="sm" c={live ? undefined : "dimmed"}>{live ? "na żywo" : "rozłączone"}</Text>
            </Group>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        {page === "wyniki" && <Wyniki {...props} />}
        {page === "alerty" && <Alerty {...props} feed={feed} live={live} />}
        {page === "kalibracja" && <Kalibracja {...props} />}
        {page === "raporty" && <Raporty {...props} />}
        {page === "operator" && <Operator {...props} />}
        {page === "notfound" && <Text c="dimmed">Nie ma takiej strony. Przejdź do <a href="#/wyniki">Wyników</a>.</Text>}
      </AppShell.Main>
    </AppShell>
  );
}
