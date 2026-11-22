// Szuflada wyniku (sticky, 480 px): naruszenia na gorze, decyzja analityka, historia.
// Tresc reklam jest niezaufana: tylko tekst (React escapuje), linki wylacznie http(s).
import { useEffect, useState } from "react";
import {
  Accordion, Alert, Anchor, Button, CloseButton, Divider, Group, Loader, NativeSelect, Paper, Select, Stack, Text,
  Textarea, Title,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import RiskBadge from "./RiskBadge.jsx";
import {
  assignFinding, getEvents, getFinding, getReviewLabels, reviewFinding, screenshotUrl, setStatus,
} from "../lib/api.js";
import { groupRules } from "../lib/findings.js";
import {
  ENGINE, MODULE_SHORT, RELATION, SCOPE, STATUS, fmtDate, publisherName, quiet, sourceLabel,
} from "../lib/labels.js";

const safeHttp = (u) => (typeof u === "string" && /^https?:\/\//i.test(u) ? u : null);
let labelsCache = null;

function RuleItem({ r }) {
  const e = r.evidence || {};
  const measured = Object.entries(e.measured || {});
  return (
    <div style={{ padding: "8px 0", borderTop: "1px solid var(--iw-border)" }}>
      <Group justify="space-between" gap="xs" wrap="nowrap" align="flex-start">
        <Text size="sm" fw={600}>{r.rule_name}</Text>
        <Text size="xs" c="dimmed" style={{ whiteSpace: "nowrap" }}>waga {r.severity ?? "—"}</Text>
      </Group>
      {e.quote && <p className="iw-quote">„{e.quote}”</p>}
      {e.summary && <Text size="sm" mt={4}>{e.summary}</Text>}
      {measured.length > 0 && (
        <Text size="xs" c="dimmed" mt={4}>{measured.map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`).join(" · ")}</Text>
      )}
      <Text size="xs" c="dimmed" mt={4}>
        {[r.legal_basis, ENGINE[r.engine] || r.engine, r.confidence != null && r.verdict !== "not_applicable" ? `pewność ${Math.round(r.confidence * 100)}%` : null]
          .filter(Boolean).join(" · ")}
      </Text>
    </div>
  );
}

function Screenshot({ documentId }) {
  const [state, setState] = useState("loading");
  useEffect(() => setState("loading"), [documentId]);
  if (state === "error") return <Text size="sm" c="dimmed">Zrzut reklamy niedostępny.</Text>;
  return (
    <a href={screenshotUrl(documentId)} target="_blank" rel="noreferrer noopener" title="Otwórz zrzut w nowej karcie">
      <img className="iw-shot" src={screenshotUrl(documentId)} alt="Zrzut reklamy (widok mobilny)"
        onError={() => setState("error")} onLoad={() => setState("ok")} />
    </a>
  );
}

export default function FindingDrawer({ id, analyst, onClose, onChanged }) {
  const [f, setF] = useState(null);
  const [error, setError] = useState(null);
  const [events, setEvents] = useState([]);
  const [labels, setLabels] = useState(labelsCache || []);
  const [label, setLabel] = useState(null);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => {
    setError(null);
    getFinding(id).then(setF).catch((e) => setError(e.message));
    getEvents(id).then((r) => setEvents(r.items || [])).catch(() => setEvents([]));
  };
  useEffect(() => {
    setF(null);
    setLabel(null);
    setNote("");
    load();
    if (!labelsCache) getReviewLabels().then((r) => { labelsCache = r.items || []; setLabels(labelsCache); }).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const act = async (fn, ok) => {
    setSaving(true);
    try {
      await fn();
      notifications.show({ color: "green", message: ok, autoClose: 4000 });
      load();
      onChanged();
    } catch (e) {
      notifications.show({ color: "red", title: "Nie zapisano", message: e.message, autoClose: 8000 });
    } finally {
      setSaving(false);
    }
  };

  if (error) return <Paper p="md" className="iw-drawer"><Group justify="space-between"><Text c="red">{error}</Text><CloseButton onClick={onClose} aria-label="Zamknij" /></Group></Paper>;
  if (!f) return <Paper p="md" className="iw-drawer"><Loader size="sm" /></Paper>;

  const doc = f.document || {};
  const rules = groupRules(f.rule_results);
  const firm = f.entities?.investment_firm;
  const adv = f.entities?.advertiser;
  const url = safeHttp(doc.url);
  const labelOptions = labels.map((l) => ({ value: l.value, label: l.label }));

  return (
    <Paper p="md" className="iw-drawer" aria-label="Szczegóły wyniku">
      <Group justify="space-between" align="flex-start" wrap="nowrap">
        <div style={{ minWidth: 0 }}>
          <Text size="xs" c="dimmed">{sourceLabel(doc.source)} · {publisherName(doc) || "publikujący nieznany"} · {fmtDate(f.created_at)}</Text>
          <Title order={3} mt={2}>{quiet(doc.title) || "Bez tytułu"}</Title>
        </div>
        <CloseButton onClick={onClose} aria-label="Zamknij szczegóły" />
      </Group>
      <Group gap="xs" mt="xs">
        <RiskBadge level={f.risk_level} score={f.risk_score} />
        <Text size="xs" c="dimmed">{f.modules?.length ? f.modules.map((m) => MODULE_SHORT[m]).join(", ") : "bez modułu"}</Text>
        <Text size="xs" c="dimmed">· {SCOPE[f.routing?.scope_gate] || "zakres nieustalony"}</Text>
      </Group>

      {f.summary && <Text size="sm" mt="sm">{f.summary}</Text>}

      <Title order={4} mt="md">Naruszenia ({rules.failed.length})</Title>
      {rules.failed.length
        ? rules.failed.map((r) => <RuleItem key={r.rule_id} r={r} />)
        : <Text size="sm" c="dimmed" mt={4}>Brak stwierdzonych naruszeń.</Text>}

      {(rules.uncertain.length > 0 || rules.notAssessed.length > 0 || rules.passed.length > 0) && (
        <Accordion variant="default" mt="xs" chevronPosition="left" multiple>
          {rules.uncertain.length > 0 && (
            <Accordion.Item value="uncertain">
              <Accordion.Control><Text size="sm">Do weryfikacji ({rules.uncertain.length})</Text></Accordion.Control>
              <Accordion.Panel>{rules.uncertain.map((r) => <RuleItem key={r.rule_id} r={r} />)}</Accordion.Panel>
            </Accordion.Item>
          )}
          {rules.passed.length > 0 && (
            <Accordion.Item value="passed">
              <Accordion.Control><Text size="sm">Zgodne ({rules.passed.length})</Text></Accordion.Control>
              <Accordion.Panel>{rules.passed.map((r) => <Text key={r.rule_id} size="sm">{r.rule_name}</Text>)}</Accordion.Panel>
            </Accordion.Item>
          )}
          {rules.notAssessed.length > 0 && (
            <Accordion.Item value="na">
              <Accordion.Control><Text size="sm" c="dimmed">Nie oceniono ({rules.notAssessed.length})</Text></Accordion.Control>
              <Accordion.Panel>
                <Text size="xs" c="dimmed" mb={4}>Brak danych do oceny (np. renderu strony albo transkrypcji). To nie jest naruszenie.</Text>
                {rules.notAssessed.map((r) => <Text key={r.rule_id} size="sm" c="dimmed">{r.rule_name}</Text>)}
              </Accordion.Panel>
            </Accordion.Item>
          )}
        </Accordion>
      )}

      <Divider my="md" />
      <Title order={4}>Podmiot i rejestr KNF</Title>
      <Stack gap={2} mt={4}>
        <Text size="sm">Firma w reklamie: <b>{firm?.name_in_ad || "nie wskazano"}</b></Text>
        <Text size="sm">Rejestr KNF: {firm?.registry_match
          ? `${firm.registry_match.official_name} (${firm.registry_match.knf_id})`
          : "brak dopasowania"}{firm?.is_authorized === false && <b style={{ color: "var(--iw-high)" }}> · brak zezwolenia</b>}</Text>
        <Text size="sm">Publikujący: {adv?.name || publisherName(doc) || "—"} · {RELATION[adv?.relation_to_firm] || "relacja nieustalona"}
          {adv?.disclosure_found === false && " · bez oznaczenia współpracy"}</Text>
      </Stack>

      <Divider my="md" />
      <Title order={4}>Materiał</Title>
      <Stack gap="xs" mt={6}>
        <Screenshot documentId={f.document_id} />
        {doc.text_excerpt && <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>{doc.text_excerpt}{doc.text_excerpt.length >= 400 ? "…" : ""}</Text>}
        {url && <Anchor size="sm" href={url} target="_blank" rel="noreferrer noopener">Otwórz źródło</Anchor>}
      </Stack>

      <Divider my="md" />
      <Title order={4}>Decyzja analityka</Title>
      {f.review ? (
        <Alert color={f.review.decision === "confirmed" ? "red" : "gray"} variant="light" mt={6} p="xs">
          <Text size="sm"><b>{STATUS[f.review.decision] || f.review.decision}</b> · {labels.find((l) => l.value === f.review.label)?.label || f.review.label}</Text>
          {f.review.note && <Text size="sm">„{f.review.note}”</Text>}
          <Text size="xs" c="dimmed">{f.review.by} · {fmtDate(f.review.at)}</Text>
        </Alert>
      ) : null}
      <Stack gap="xs" mt={6}>
        <Select label="Ocena" placeholder="Wybierz etykietę" data={labelOptions} value={label} onChange={setLabel} searchable={false} />
        <Textarea label="Notatka" placeholder={label === "other" ? "Opisz błąd (wymagane)" : "Podstawa decyzji (opcjonalnie)"}
          autosize minRows={2} maxLength={2000} value={note} onChange={(e) => setNote(e.currentTarget.value)} />
        <Button disabled={!label || (label === "other" && !note.trim())} loading={saving}
          onClick={() => act(() => reviewFinding(f.id, label, note.trim(), analyst), "Ocena zapisana.")}>
          Zapisz ocenę jako {analyst}
        </Button>
        <Group grow>
          <NativeSelect label="Status" value={f.status} disabled={saving}
            data={Object.entries(STATUS).filter(([k]) => !["confirmed", "dismissed"].includes(k) || k === f.status)
              .map(([value, l]) => ({ value, label: l }))}
            onChange={(e) => act(() => setStatus(f.id, e.currentTarget.value), "Status zmieniony.")} />
          <NativeSelect label="Przypisany" value={f.assignee || ""} disabled={saving}
            data={[{ value: "", label: "nieprzypisany" }, ...[...new Set(["analityk.a", "analityk.b", "analityk.c", analyst, f.assignee].filter(Boolean))].map((a) => ({ value: a, label: a }))]}
            onChange={(e) => act(() => assignFinding(f.id, e.currentTarget.value || null, analyst), "Przypisanie zapisane.")} />
        </Group>
        <Text size="xs" c="dimmed">„Potwierdzony” i „odrzucony” ustawia wyłącznie ocena analityka.</Text>
      </Stack>

      <Divider my="md" />
      <Title order={4}>Historia</Title>
      <Stack gap={2} mt={4}>
        <Text size="xs" c="dimmed">{fmtDate(f.created_at)} · system: wykrycie i analiza</Text>
        {events.map((e, i) => (
          <Text key={i} size="xs" c="dimmed">{fmtDate(e.at)} · {e.actor || "system"}: {e.action === "review" ? `ocena ${e.detail?.label || ""}` : e.action === "assign" ? (e.detail?.assignee ? `przypisano ${e.detail.assignee}` : "zwolniono") : e.action === "status" ? `status ${STATUS[e.detail?.status] || e.detail?.status}` : e.action}</Text>
        ))}
      </Stack>
    </Paper>
  );
}
