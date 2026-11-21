import { RISK, RISK_COLOR, STATUS } from "../../lib/labels.js";

export function RiskBadge({ level, score }) {
  return (
    <span className="badge" style={{ background: RISK_COLOR[level] }}>
      {RISK[level]}{score != null ? ` · ${score.toFixed(1)}` : ""}
    </span>
  );
}

export function StatusBadge({ status }) {
  return <span className={`badge status-${status}`}>{STATUS[status]}</span>;
}
