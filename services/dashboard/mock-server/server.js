// Serwer mock InvestWatch: REST w ksztalcie services/api + Socket.io z alertami.
// Uruchom: npm run mock  (port MOCK_PORT, domyslnie 4000).
//
// PUNKTY POLACZENIA Z BAZA (do podmiany przy integracji):
//   [DB-1] GET   /api/findings           -> SELECT findings f JOIN documents d (store.list_findings)
//   [DB-2] GET   /api/findings/:id       -> store.get_finding
//   [DB-3] PATCH /api/findings/:id       -> UPDATE findings SET status/assignee (store.update_status)
//   [DB-4] GET   /api/stats              -> agregaty (services/api /stats)
//   [DB-5] GET   /api/stats/trend        -> GROUP BY date_trunc('day', created_at), risk_level  (NOWY endpoint)
//   [DB-6] GET   /api/calibration        -> zbior zloty (fixtures/gold/labels.json)
//   [DB-7] socket.io "finding.high"      -> emitowany przy INSERT findingu z risk_level=high
//          (services/api ma dzis natywny WS /ws/alerts; patrz src/api/socket.js)
import http from "node:http";
import { Server } from "socket.io";
import { makeFindings, makeFinding, makeGold, STATUSES } from "./data.js";

const PORT = Number(process.env.MOCK_PORT || 4000);
const ALERT_EVERY_MS = Number(process.env.MOCK_ALERT_MS || 25000);

const findings = makeFindings();
const gold = makeGold();

const listParam = (sp, k) => sp.getAll(k).flatMap((v) => v.split(",")).filter(Boolean);

function applyFilters(items, sp) {
  const risk = listParam(sp, "risk_level");
  const status = listParam(sp, "status");
  const source = listParam(sp, "source");
  const module = listParam(sp, "module").map(Number);
  const from = sp.get("from");
  const to = sp.get("to");
  const q = (sp.get("q") || "").toLowerCase();
  return items.filter(
    (f) =>
      (!risk.length || risk.includes(f.risk_level)) &&
      (!status.length || status.includes(f.status)) &&
      (!source.length || source.includes(f.document.source)) &&
      (!module.length || f.modules.some((m) => module.includes(m))) &&
      (!from || f.created_at >= from) &&
      (!to || f.created_at <= to) &&
      (!q ||
        [f.document.title, f.document.publisher, f.routing.reason, f.entities.investment_firm.name_in_ad]
          .join(" ")
          .toLowerCase()
          .includes(q)),
  );
}

const count = (arr, key) => arr.reduce((acc, x) => ((acc[key(x)] = (acc[key(x)] || 0) + 1), acc), {});

function stats(items) {
  const failed = {};
  for (const f of items)
    for (const r of f.rule_results)
      if (r.verdict === "fail") (failed[r.rule_id] ||= { rule_id: r.rule_id, rule_name: r.rule_name, count: 0 }).count++;
  return {
    total: items.length,
    by_risk_level: count(items, (f) => f.risk_level),
    by_status: count(items, (f) => f.status),
    by_source: count(items, (f) => f.document.source),
    by_module: count(items.flatMap((f) => f.modules), (m) => String(m)),
    failed_rules: Object.values(failed).sort((a, b) => b.count - a.count),
  };
}

function trend(items) {
  const days = {};
  for (const f of items) {
    const d = f.created_at.slice(0, 10);
    days[d] ||= { date: d, high: 0, medium: 0, low: 0, total: 0 };
    days[d][f.risk_level]++;
    days[d].total++;
  }
  return Object.values(days).sort((a, b) => a.date.localeCompare(b.date));
}

const send = (res, code, body) => {
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*" });
  res.end(JSON.stringify(body));
};

const readBody = (req) =>
  new Promise((resolve) => {
    let raw = "";
    req.on("data", (c) => (raw += c));
    req.on("end", () => {
      try { resolve(JSON.parse(raw || "{}")); } catch { resolve({}); }
    });
  });

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  const p = url.pathname.replace(/^\/api/, "");
  const sp = url.searchParams;
  if (req.method === "OPTIONS") {
    res.writeHead(204, { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET,PATCH", "Access-Control-Allow-Headers": "Content-Type" });
    return res.end();
  }
  if (req.method === "GET" && p === "/health") return send(res, 200, { status: "ok", db: "mock" });
  if (req.method === "GET" && p === "/findings") {
    const items = applyFilters(findings, sp);
    const limit = Math.min(Number(sp.get("limit") || 100), 500);
    const offset = Number(sp.get("offset") || 0);
    return send(res, 200, { items: items.slice(offset, offset + limit), total: items.length, limit, offset });
  }
  const m = p.match(/^\/findings\/([\w-]+)$/);
  if (m) {
    const f = findings.find((x) => x.id === m[1]);
    if (!f) return send(res, 404, { detail: `Brak findingu ${m[1]}` });
    if (req.method === "GET") return send(res, 200, f);
    if (req.method === "PATCH") {
      const body = await readBody(req);
      if (body.status && !STATUSES.includes(body.status)) return send(res, 422, { detail: "Zly status" });
      if (body.status) f.status = body.status;
      if ("assignee" in body) f.assignee = body.assignee || null;
      io.emit("finding.updated", { finding_id: f.id, status: f.status, assignee: f.assignee });
      return send(res, 200, { id: f.id, status: f.status, assignee: f.assignee });
    }
  }
  if (req.method === "GET" && p === "/stats") return send(res, 200, stats(applyFilters(findings, sp)));
  if (req.method === "GET" && p === "/stats/trend") return send(res, 200, { items: trend(applyFilters(findings, sp)) });
  if (req.method === "GET" && p === "/calibration") return send(res, 200, { items: gold, source: "mock", available: true });
  send(res, 404, { detail: "Not found" });
});

const io = new Server(server, { cors: { origin: "*" } });
io.on("connection", (s) => s.emit("hello", { clients: io.engine.clientsCount }));

// Symulacja: co ALERT_EVERY_MS nowy finding; jesli high -> alert na zywo.
setInterval(() => {
  const f = makeFinding(new Date());
  f.status = "new";
  findings.unshift(f);
  if (f.risk_level === "high") {
    io.emit("finding.high", {
      type: "finding.high",
      finding_id: f.id,
      risk_score: f.risk_score,
      risk_level: f.risk_level,
      primary_module: f.primary_module,
      routing_reason: f.routing.reason,
      title: f.document.title,
      source: f.document.source,
      created_at: f.created_at,
    });
  } else {
    io.emit("finding.new", { finding_id: f.id, risk_level: f.risk_level });
  }
}, ALERT_EVERY_MS);

const HOST = process.env.MOCK_HOST || "127.0.0.1"; // w kontenerze: 0.0.0.0
server.listen(PORT, HOST, () => console.log(`mock api: http://${HOST}:${PORT}/api/findings`));
