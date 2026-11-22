// Alerty: strumien WebSocket (finding.high) jako tabela + otwarte wyniki wysokiego ryzyka z bazy.
import { useEffect, useState } from "react";
import { Alert, Anchor, Button, Group, Paper, Stack, Table, Text, Title } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import RiskBadge from "../components/RiskBadge.jsx";
import { assignFinding, listFindings } from "../lib/api.js";
import { fmtShort, publisherName, quiet, sourceLabel } from "../lib/labels.js";

const open = (id) => { window.location.hash = `#/wyniki?id=${encodeURIComponent(id)}`; };

export default function Alerty({ feed, live, refreshKey, refresh, analyst }) {
  const [queue, setQueue] = useState({ items: [], total: 0 });
  const [error, setError] = useState(null);
  useEffect(() => {
    listFindings({ risk_level: "high", status: ["new", "triage", "in_review"], limit: 100 })
      .then((d) => { setQueue(d); setError(null); })
      .catch((e) => setError(e.message));
  }, [refreshKey]);

  const take = async (id) => {
    try {
      await assignFinding(id, analyst, analyst);
      notifications.show({ color: "green", message: `Przejęte przez ${analyst}.`, autoClose: 4000 });
      refresh();
    } catch (e) {
      notifications.show({ color: "red", title: "Nie przejęto", message: e.message, autoClose: 8000 });
    }
  };

  return (
    <Stack gap="sm">
      <div>
        <Title order={1}>Alerty</Title>
        <Text size="sm" c="dimmed">Wyniki wysokiego ryzyka: nowe na żywo z WebSocket i otwarte sprawy z bazy.</Text>
      </div>

      <Paper p="sm">
        <Group justify="space-between" mb="xs">
          <Title order={4}>Na żywo</Title>
          <Text size="xs" c="dimmed">{live ? "połączono z /ws/alerts" : "rozłączone, ponawiam połączenie"}</Text>
        </Group>
        {feed.length ? (
          <Table className="iw-table" verticalSpacing={6} highlightOnHover>
            <Table.Thead><Table.Tr><Table.Th>Czas</Table.Th><Table.Th>Ryzyko</Table.Th><Table.Th>Materiał</Table.Th><Table.Th>Naruszone reguły</Table.Th><Table.Th /></Table.Tr></Table.Thead>
            <Table.Tbody>
              {feed.map((a) => (
                <Table.Tr key={a.finding_id}>
                  <Table.Td>{fmtShort(a.created_at || a.received_at)}</Table.Td>
                  <Table.Td><RiskBadge level="high" score={a.risk_score} /></Table.Td>
                  <Table.Td><Text size="sm" lineClamp={1}>{quiet(a.title) || a.document_id}</Text><Text size="xs" c="dimmed">{sourceLabel(a.source)}</Text></Table.Td>
                  <Table.Td><Text size="xs" lineClamp={2}>{(a.failed_rule_names || a.failed_rules || []).join(", ") || "—"}</Text></Table.Td>
                  <Table.Td><Group gap={4} wrap="nowrap"><Button size="xs" variant="default" onClick={() => take(a.finding_id)}>Przejmij</Button><Button size="xs" onClick={() => open(a.finding_id)}>Otwórz</Button></Group></Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        ) : <Text size="sm" c="dimmed">Od otwarcia panelu nie przyszedł żaden nowy alert.</Text>}
      </Paper>

      <Paper p="sm">
        <Title order={4} mb="xs">Otwarte sprawy wysokiego ryzyka ({queue.total})</Title>
        {error && <Alert color="gray" variant="light">{error}</Alert>}
        {queue.items.length ? (
          <Table className="iw-table" verticalSpacing={6} highlightOnHover>
            <Table.Thead><Table.Tr><Table.Th>Wykryto</Table.Th><Table.Th>Ryzyko</Table.Th><Table.Th>Materiał</Table.Th><Table.Th>Przypisany</Table.Th><Table.Th /></Table.Tr></Table.Thead>
            <Table.Tbody>
              {queue.items.map((f) => (
                <Table.Tr key={f.id}>
                  <Table.Td>{fmtShort(f.created_at)}</Table.Td>
                  <Table.Td><RiskBadge level={f.risk_level} score={f.risk_score} /></Table.Td>
                  <Table.Td><Anchor size="sm" onClick={() => open(f.id)} lineClamp={1}>{quiet(f.document?.title) || "Bez tytułu"}</Anchor>
                    <Text size="xs" c="dimmed">{sourceLabel(f.document?.source)} · {publisherName(f.document) || "—"}</Text></Table.Td>
                  <Table.Td>{f.assignee || <Text size="sm" c="dimmed">—</Text>}</Table.Td>
                  <Table.Td>{f.assignee !== analyst && <Button size="xs" variant="default" onClick={() => take(f.id)}>Przejmij</Button>}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        ) : !error && <Text size="sm" c="dimmed">Brak otwartych spraw wysokiego ryzyka.</Text>}
      </Paper>
    </Stack>
  );
}
