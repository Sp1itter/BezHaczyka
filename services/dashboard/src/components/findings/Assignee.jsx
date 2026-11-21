import { ANALYSTS, ASSIGNED_BY } from "../../lib/labels.js";

// Kto zajmuje sie alertem. AI moze tylko zasugerowac osobe; przypisanie zapisuje czlowiek.
export function AssigneeTag({ finding: f }) {
  if (!f.assignee) return <span className="muted">—</span>;
  return (
    <span>
      {f.assignee}
      {f.assigned_by && <span className={`tag ${f.assigned_by === "ai" ? "ai" : "human"}`}>{ASSIGNED_BY[f.assigned_by]}</span>}
    </span>
  );
}

export function AssigneeSelect({ finding: f, currentUser, onAssign }) {
  const suggestion = f.ai_suggestion?.assignee;
  const mine = f.assignee && f.assignee === currentUser;
  const options = [...new Set([...ANALYSTS, currentUser, f.assignee].filter(Boolean))];
  return (
    <span className="assign" onClick={(e) => e.stopPropagation()}>
      {!mine && currentUser && (
        <button className="btn small take" onClick={() => onAssign(f.id, currentUser)}>
          {f.assignee ? "Przejmij" : "Zajmuję się"}
        </button>
      )}
      {mine && <button className="btn small" onClick={() => onAssign(f.id, null)}>Zwolnij</button>}
      <select value={f.assignee || ""} onChange={(e) => onAssign(f.id, e.target.value || null)}>
        <option value="">— nieprzypisane —</option>
        {options.map((a) => <option key={a} value={a}>{a}{a === suggestion ? " (sugestia AI)" : ""}</option>)}
      </select>
      {f.assigned_by === "ai" && (
        <button className="btn small" onClick={() => onAssign(f.id, f.assignee)}>Zatwierdź</button>
      )}
    </span>
  );
}
