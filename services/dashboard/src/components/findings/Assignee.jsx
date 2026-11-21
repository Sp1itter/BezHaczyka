import { ANALYSTS, ASSIGNED_BY } from "../../lib/labels.js";

// Przypisanie: AI moze zaproponowac/wstepnie przypisac, czlowiek zatwierdza lub zmienia.
export function AssigneeTag({ finding: f }) {
  if (!f.assignee) return <span className="muted">—</span>;
  return (
    <span>
      {f.assignee}
      <span className={`tag ${f.assigned_by === "ai" ? "ai" : "human"}`}>{ASSIGNED_BY[f.assigned_by]}</span>
    </span>
  );
}

export function AssigneeSelect({ finding: f, onAssign }) {
  const suggestion = f.ai_suggestion?.assignee;
  return (
    <span className="assign" onClick={(e) => e.stopPropagation()}>
      <select value={f.assignee || ""} onChange={(e) => onAssign(f.id, e.target.value || null)}>
        <option value="">— nieprzypisane —</option>
        {ANALYSTS.map((a) => <option key={a} value={a}>{a}{a === suggestion ? " (sugestia AI)" : ""}</option>)}
      </select>
      {(f.assigned_by === "ai" || (!f.assignee && suggestion)) && (
        <button className="btn small" onClick={() => onAssign(f.id, f.assignee || suggestion)}>
          {f.assigned_by === "ai" ? "Zatwierdź" : `Przyjmij: ${suggestion}`}
        </button>
      )}
    </span>
  );
}
