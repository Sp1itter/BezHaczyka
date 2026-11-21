import { STATUS } from "../../lib/labels.js";

export default function StatusSelect({ value, onChange, disabled }) {
  return (
    <select className={`status-select status-${value}`} value={value} disabled={disabled}
      onClick={(e) => e.stopPropagation()} onChange={(e) => onChange(e.target.value)}>
      {Object.entries(STATUS).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
    </select>
  );
}
