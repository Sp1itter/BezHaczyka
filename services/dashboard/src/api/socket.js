// Alerty na zywo: natywny WebSocket /ws/alerts (tak jak services/api). [DB-7]
// Wiadomosci: {type:"hello"}, {type:"finding.high", finding_id, risk_score, title, routing_reason, ...}.
// Mock wysyla dodatkowo "finding.new" i "finding.updated".
export function connectAlerts({ onHigh, onNew, onUpdated, onState }) {
  let ws, timer, closed = false;
  const open = () => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/ws/alerts`);
    ws.onopen = () => onState?.(true);
    ws.onmessage = (e) => {
      let m;
      try { m = JSON.parse(e.data); } catch { return; }
      if (m.type === "finding.high") onHigh?.(m);
      else if (m.type === "finding.new") onNew?.(m);
      else if (m.type === "finding.updated") onUpdated?.(m);
    };
    ws.onclose = () => {
      onState?.(false);
      if (!closed) timer = setTimeout(open, 3000); // ponowne laczenie
    };
  };
  open();
  return () => { closed = true; clearTimeout(timer); ws?.close(); };
}
