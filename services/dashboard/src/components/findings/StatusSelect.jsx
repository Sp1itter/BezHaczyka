import { HUMAN_ONLY, STATUS } from "../../lib/labels.js";

// Statusy robocze. "Potwierdzone"/"Odrzucone" tylko przez weryfikacje czlowieka (ReviewActions).
export default function StatusSelect({ value, onChange, disabled }) {
  const locked = disabled || HUMAN_ONLY.includes(value);
  return (
    <select className={`status-select status-${value}`} value={value} disabled={locked}
      title={HUMAN_ONLY.includes(value) ? "Status po weryfikacji człowieka" : undefined}
      onClick={(e) => e.stopPropagation()} onChange={(e) => onChange(e.target.value)}>
      {Object.entries(STATUS).map(([k, label]) => (
        <option key={k} value={k} disabled={HUMAN_ONLY.includes(k)}>{label}</option>
      ))}
    </select>
  );
}
