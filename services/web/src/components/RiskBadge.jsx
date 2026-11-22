import { Badge } from "@mantine/core";
import { RISK_LABEL, TOKENS } from "../theme.js";

// Kolor ryzyka zawsze z etykieta tekstowa (plan, par. 9); "niskie" jest szare, bo nie znaczy "dobre".
export default function RiskBadge({ level, score }) {
  const color = TOKENS.risk[level] || TOKENS.risk.low;
  return (
    <Badge variant="outline" radius="xs" size="sm"
      styles={{ root: { color, borderColor: color, background: "#fff", textTransform: "none", fontWeight: 600 } }}>
      {RISK_LABEL[level] || "—"}{score != null ? ` · ${Number(score).toFixed(1).replace(".", ",")}` : ""}
    </Badge>
  );
}
